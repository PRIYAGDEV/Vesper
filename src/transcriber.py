import logging
import os
import threading
from pathlib import Path
from typing import Optional, Union

import numpy as np

# Prevent hf_xet hangs on Windows
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def setup_cuda_dll_paths():
    """Ensure Windows can locate nvidia-cublas and nvidia-cudnn DLLs."""
    import sys
    if sys.platform == "win32":
        from pathlib import Path
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

logger = logging.getLogger("WisprClone.Transcriber")


def is_cuda_fully_functional() -> bool:
    setup_cuda_dll_paths()
    """Check if CUDA and required cuBLAS DLLs are actually loadable and functioning."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() <= 0:
            return False
        # Test if cuBLAS can actually be loaded
        import ctypes
        try:
            # Check standard cuBLAS DLL names
            for dll_name in ("cublas64_12.dll", "cublas64_11.dll"):
                try:
                    ctypes.CDLL(dll_name)
                    return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
    except Exception:
        return False


class WhisperTranscriber:
    """Manages the faster-whisper local model and provides fast transcription with VAD."""

    def __init__(
        self,
        model_size: str = "base.en",
        device: Optional[str] = None,
        compute_type: Optional[str] = None
    ):
        self.model_size = model_size
        self._requested_device = device
        self._requested_compute = compute_type
        self.model: Optional[WhisperModel] = None
        self.active_device = "cpu"
        self.active_compute = "int8"
        self._lock = threading.Lock()
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

    def load_model(self) -> None:
        """Load the faster-whisper model into memory."""
        with self._lock:
            if self.model is not None:
                return

            self._is_loading = True
            dev, comp = self._determine_device_and_compute()
            logger.info(f"Loading faster-whisper model '{self.model_size}' on {dev} ({comp})...")

            # Check local model folders or cached HuggingFace snapshots
            target_model = self.model_size

            # Check candidate local paths
            candidate_dirs = [
                Path("models") / self.model_size,
                Path(__file__).resolve().parent.parent / "models" / self.model_size,
            ]
            import sys
            if getattr(sys, "frozen", False):
                candidate_dirs.insert(0, Path(sys.executable).parent / "models" / self.model_size)
                candidate_dirs.insert(1, Path(sys.executable).parent.parent / "models" / self.model_size)

            local_found = False
            for c_path in candidate_dirs:
                if c_path.exists() and (c_path / "model.bin").exists():
                    bin_size = (c_path / "model.bin").stat().st_size
                    min_exp = (
                        1_400_000_000 if self.model_size == "medium"
                        else 450_000_000 if self.model_size == "small"
                        else 50_000_000
                    )
                    if bin_size >= min_exp:
                        target_model = str(c_path.resolve())
                        local_found = True
                        logger.info(f"Using local model from: {target_model}")
                        break

            # If user selected medium but it's not downloaded, avoid 1.5GB hang
            if not local_found and self.model_size == "medium":
                hf_med = Path.home() / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-medium" / "snapshots"
                has_complete_med = False
                if hf_med.exists():
                    for snap in hf_med.iterdir():
                        if snap.is_dir() and (snap / "model.bin").exists():
                            if (snap / "model.bin").stat().st_size >= 1_400_000_000:
                                has_complete_med = True
                                break
                if not has_complete_med:
                    logger.warning("Medium model (~1.5GB) is not fully downloaded. Using 'base' multilingual model for instant response.")
                    target_model = "base"

            try:
                self.model = WhisperModel(target_model, device=dev, compute_type=comp, cpu_threads=4)
                self.active_device = dev
                self.active_compute = comp
                logger.info(f"Model '{target_model}' loaded successfully on {dev}.")
            except Exception as e:
                if dev == "cuda":
                    logger.warning(f"CUDA failed to load ({e}). Falling back to CPU int8...")
                    self.model = WhisperModel(target_model, device="cpu", compute_type="int8", cpu_threads=4)
                    self.active_device = "cpu"
                    self.active_compute = "int8"
                    logger.info(f"Model '{target_model}' loaded successfully on CPU fallback.")
                else:
                    logger.warning(f"Failed to load {target_model} ({e}). Falling back to 'base' model...")
                    self.model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)
                    self.active_device = "cpu"
                    self.active_compute = "int8"
                    logger.info("Base model loaded successfully on CPU fallback.")
            finally:
                self._is_loading = False

    def change_model(self, new_model_size: str) -> None:
        """Switch to a different model size."""
        with self._lock:
            if new_model_size != self.model_size:
                logger.info(f"Switching model from '{self.model_size}' to '{new_model_size}'")
                self.model_size = new_model_size
                self.model = None
                self.load_model()

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        language: Optional[str] = "en",
        task: str = "transcribe",
        vad_filter: bool = True
    ) -> str:
        """Transcribe or translate audio (file path or 16kHz float32 numpy array) to text."""
        if self.model is None:
            self.load_model()

        if isinstance(audio, (str, Path)):
            audio_target = str(audio)
        else:
            audio_target = audio.astype(np.float32)

        vad_params = dict(
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=500,
            speech_pad_ms=250
        ) if vad_filter else None

        # Optimized English dictation prompt for high accuracy
        prompt = "Clear, articulate voice dictation with proper capitalization and punctuation."

        with self._lock:
            try:
                segments, info = self.model.transcribe(
                    audio_target,
                    language=language if language and language != "auto" else None,
                    task=task,
                    vad_filter=vad_filter,
                    vad_parameters=vad_params,
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    condition_on_previous_text=False,
                    repetition_penalty=1.3,
                    no_repeat_ngram_size=3,
                    compression_ratio_threshold=2.2,
                    hallucination_silence_threshold=1.5,
                    no_speech_threshold=0.6,
                    initial_prompt=prompt
                )
                texts = [s.text.strip() for s in segments if s.text.strip()]
                result_text = " ".join(texts).strip()
            except RuntimeError as e:
                if "cublas" in str(e).lower() or "cuda" in str(e).lower():
                    logger.warning(f"CUDA runtime error encountered ({e}). Switching to CPU int8...")
                    self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8", cpu_threads=4)
                    self.active_device = "cpu"
                    self.active_compute = "int8"
                    segments, info = self.model.transcribe(
                        audio_target,
                        language=language if language and language != "auto" else None,
                        task=task,
                        vad_filter=vad_filter,
                        vad_parameters=vad_params,
                        beam_size=5,
                        best_of=5,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        repetition_penalty=1.3,
                        no_repeat_ngram_size=3,
                        compression_ratio_threshold=2.2,
                        hallucination_silence_threshold=1.5,
                        no_speech_threshold=0.6,
                        initial_prompt=prompt
                    )
                    texts = [s.text.strip() for s in segments if s.text.strip()]
                    result_text = " ".join(texts).strip()
                else:
                    raise e

            logger.info(f"Transcription ({info.duration:.2f}s audio, task={task}, lang={info.language}): '{result_text}'")
            return result_text
