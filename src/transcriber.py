import logging
import os
import sys
import threading
import wave
from pathlib import Path
from typing import Optional, Union

import numpy as np
import scipy.signal

# Prevent hf_xet hangs on Windows
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def setup_cuda_dll_paths():
    """Ensure Windows can locate nvidia-cublas and nvidia-cudnn DLLs."""
    if sys.platform == "win32":
        candidate_dirs = [
            Path(sys.prefix) / "Lib" / "site-packages" / "nvidia" / "cublas" / "bin",
            Path(sys.prefix) / "Lib" / "site-packages" / "nvidia" / "cudnn" / "bin",
            Path(__file__).resolve().parent.parent / ".venv" / "Lib" / "site-packages" / "nvidia" / "cublas" / "bin",
            Path(__file__).resolve().parent.parent / ".venv" / "Lib" / "site-packages" / "nvidia" / "cudnn" / "bin",
        ]
        for c_dir in candidate_dirs:
            if c_dir.exists():
                s_dir = str(c_dir.resolve())
                try:
                    os.add_dll_directory(s_dir)
                except Exception:
                    pass
                if s_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = s_dir + os.pathsep + os.environ.get("PATH", "")


setup_cuda_dll_paths()

from faster_whisper import WhisperModel
from src.config import get_app_data_dir

logger = logging.getLogger("WisprClone.Transcriber")


def is_cuda_fully_functional() -> bool:
    """Check if CUDA and required cuBLAS DLLs are actually loadable and functioning."""
    setup_cuda_dll_paths()
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() <= 0:
            return False
        if sys.platform == "win32":
            import ctypes

            for dll_name in ("cublas64_12.dll", "cublas64_11.dll"):
                try:
                    ctypes.CDLL(dll_name)
                    return True
                except Exception:
                    continue
            return False
        return True
    except Exception:
        return False


def _optimal_cpu_threads() -> int:
    count = os.cpu_count() or 4
    return max(2, min(8, count // 2 if count >= 4 else count))


def _load_wav_as_float32_16k(path: Union[str, Path]) -> Optional[np.ndarray]:
    """Load a PCM WAV file directly into a 16kHz mono float32 numpy array without relying on PyAV."""
    try:
        with wave.open(str(path), "rb") as wf:
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            raw_bytes = wf.readframes(nframes)

        if sampwidth == 2:
            audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif sampwidth == 1:
            audio = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            return None

        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1, dtype=np.float32)

        if framerate != 16000 and len(audio) > 0:
            gcd = int(np.gcd(16000, framerate))
            audio = scipy.signal.resample_poly(audio, 16000 // gcd, framerate // gcd).astype(np.float32)

        return audio
    except Exception as e:
        logger.debug(f"Direct WAV loader fallback to PyAV for {path}: {e}")
        return None


class WhisperTranscriber:
    """Manages the faster-whisper local model and provides fast transcription with VAD."""

    def __init__(
        self,
        model_size: str = "base.en",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        self.model_size = model_size
        self._requested_device = device
        self._requested_compute = compute_type
        self.model: Optional[WhisperModel] = None
        self.active_device = "cpu"
        self.active_compute = "int8"
        self._lock = threading.RLock()
        self._is_loading = False

    def _determine_device_and_compute(self) -> tuple[str, str]:
        if self._requested_device:
            dev = self._requested_device
            comp = self._requested_compute or ("float16" if dev == "cuda" else "int8")
            return dev, comp

        if is_cuda_fully_functional():
            logger.info("CUDA and cuBLAS available. Using CUDA float16.")
            return "cuda", "float16"

        logger.info("Using high-performance CPU with int8 quantization.")
        return "cpu", "int8"

    def _resolve_model_target(self, model_size: str) -> str:
        """Resolve local model directory if present, otherwise return model identifier."""
        candidate_dirs = [
            Path("models") / model_size,
            Path(__file__).resolve().parent.parent / "models" / model_size,
            get_app_data_dir() / "models" / model_size,
        ]
        if getattr(sys, "frozen", False):
            candidate_dirs.insert(0, Path(sys.executable).resolve().parent / "models" / model_size)
            candidate_dirs.insert(1, Path(sys.executable).resolve().parent.parent / "models" / model_size)
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                candidate_dirs.insert(0, Path(meipass) / "models" / model_size)

        min_exp = (
            1_400_000_000 if model_size == "medium"
            else 450_000_000 if model_size.startswith("small")
            else 120_000_000 if model_size.startswith("base")
            else 50_000_000
        )

        for c_path in candidate_dirs:
            try:
                if c_path.exists() and (c_path / "model.bin").exists():
                    bin_size = (c_path / "model.bin").stat().st_size
                    if bin_size >= min_exp:
                        resolved = str(c_path.resolve())
                        logger.info(f"Using local model from: {resolved}")
                        return resolved
            except Exception:
                continue

        # If user selected medium but it's not downloaded, avoid 1.5GB hang
        if model_size == "medium":
            hf_med = (
                Path.home()
                / ".cache"
                / "huggingface"
                / "hub"
                / "models--Systran--faster-whisper-medium"
                / "snapshots"
            )
            has_complete_med = False
            if hf_med.exists():
                for snap in hf_med.iterdir():
                    if snap.is_dir() and (snap / "model.bin").exists():
                        if (snap / "model.bin").stat().st_size >= 1_400_000_000:
                            has_complete_med = True
                            break
            if not has_complete_med:
                logger.warning(
                    "Medium model (~1.5GB) is not fully downloaded. Using 'base' multilingual model for instant response."
                )
                return self._resolve_model_target("base")

        return model_size

    def load_model(self) -> None:
        """Load the faster-whisper model into memory."""
        with self._lock:
            if self.model is not None:
                return

            self._is_loading = True
            dev, comp = self._determine_device_and_compute()
            cpu_threads = _optimal_cpu_threads()
            logger.info(
                f"Loading faster-whisper model '{self.model_size}' on {dev} ({comp}, threads={cpu_threads})..."
            )

            target_model = self._resolve_model_target(self.model_size)

            try:
                self.model = WhisperModel(target_model, device=dev, compute_type=comp, cpu_threads=cpu_threads)
                self.active_device = dev
                self.active_compute = comp
                logger.info(f"Model '{target_model}' loaded successfully on {dev}.")
            except Exception as e:
                if dev == "cuda":
                    logger.warning(f"CUDA failed to load ({e}). Falling back to CPU int8...")
                    try:
                        self.model = WhisperModel(
                            target_model, device="cpu", compute_type="int8", cpu_threads=cpu_threads
                        )
                        self.active_device = "cpu"
                        self.active_compute = "int8"
                        logger.info(f"Model '{target_model}' loaded successfully on CPU fallback.")
                    except Exception as cpu_err:
                        logger.warning(f"Failed to load {target_model} on CPU ({cpu_err}). Falling back to 'base'...")
                        fallback_target = self._resolve_model_target("base")
                        self.model = WhisperModel(
                            fallback_target, device="cpu", compute_type="int8", cpu_threads=cpu_threads
                        )
                        self.active_device = "cpu"
                        self.active_compute = "int8"
                        logger.info("Base model loaded successfully on CPU fallback.")
                else:
                    logger.warning(f"Failed to load {target_model} ({e}). Falling back to 'base' model...")
                    fallback_target = self._resolve_model_target("base")
                    self.model = WhisperModel(
                        fallback_target, device="cpu", compute_type="int8", cpu_threads=cpu_threads
                    )
                    self.active_device = "cpu"
                    self.active_compute = "int8"
                    logger.info("Base model loaded successfully on CPU fallback.")
            finally:
                self._is_loading = False

    def change_model(self, new_model_size: str) -> None:
        """Switch to a different model size safely without deadlocking."""
        with self._lock:
            if new_model_size != self.model_size or self.model is None:
                logger.info(f"Switching model from '{self.model_size}' to '{new_model_size}'")
                self.model_size = new_model_size
                self.model = None
                self.load_model()

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        language: Optional[str] = "en",
        task: str = "transcribe",
        vad_filter: bool = True,
    ) -> str:
        """Transcribe or translate audio (file path or 16kHz float32 numpy array) to text."""
        with self._lock:
            if self.model is None:
                self.load_model()

            if isinstance(audio, (str, Path)):
                wav_array = _load_wav_as_float32_16k(audio)
                audio_target: Union[str, np.ndarray] = wav_array if wav_array is not None else str(audio)
            else:
                audio_target = audio.astype(np.float32)

            vad_params = (
                dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    min_silence_duration_ms=500,
                    speech_pad_ms=250,
                )
                if vad_filter
                else None
            )

            if task == "translate":
                prompt = "Translate clear Hindi speech into fluent, natural English with proper punctuation."
            else:
                prompt = "Clear, articulate voice dictation with proper capitalization and punctuation."

            # Use faster beam_size=3 on CPU for responsive transcription; beam_size=5 on CUDA
            beam_size = 5 if self.active_device == "cuda" else 3

            def _run_transcribe(use_vad: bool):
                return self.model.transcribe(
                    audio_target,
                    language=language if language and language != "auto" else None,
                    task=task,
                    vad_filter=use_vad,
                    vad_parameters=vad_params if use_vad else None,
                    beam_size=beam_size,
                    best_of=beam_size,
                    temperature=0.0,
                    condition_on_previous_text=False,
                    repetition_penalty=1.3,
                    no_repeat_ngram_size=3,
                    compression_ratio_threshold=2.2,
                    hallucination_silence_threshold=1.5,
                    no_speech_threshold=0.6,
                    initial_prompt=prompt,
                )

            try:
                segments, info = _run_transcribe(vad_filter)
                texts = [s.text.strip() for s in segments if s.text.strip()]
                result_text = " ".join(texts).strip()
            except Exception as e:
                err_str = str(e).lower()
                if "cublas" in err_str or "cuda" in err_str:
                    logger.warning(f"CUDA runtime error encountered ({e}). Switching to CPU int8...")
                    cpu_threads = _optimal_cpu_threads()
                    target_model = self._resolve_model_target(self.model_size)
                    self.model = WhisperModel(
                        target_model, device="cpu", compute_type="int8", cpu_threads=cpu_threads
                    )
                    self.active_device = "cpu"
                    self.active_compute = "int8"
                    beam_size = 3
                    segments, info = _run_transcribe(vad_filter)
                    texts = [s.text.strip() for s in segments if s.text.strip()]
                    result_text = " ".join(texts).strip()
                elif vad_filter and ("onnx" in err_str or "silero" in err_str or "vad" in err_str):
                    logger.warning(f"VAD filter error encountered ({e}). Retrying without VAD filter...")
                    segments, info = _run_transcribe(False)
                    texts = [s.text.strip() for s in segments if s.text.strip()]
                    result_text = " ".join(texts).strip()
                else:
                    raise

            logger.info(
                f"Transcription ({info.duration:.2f}s audio, task={task}, lang={info.language}): '{result_text}'"
            )
            return result_text
