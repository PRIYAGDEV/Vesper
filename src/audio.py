import logging
import queue
import threading
import wave
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import scipy.signal

try:
    import sounddevice as sd
except Exception:
    sd = None  # type: ignore

logger = logging.getLogger("WisprClone.Audio")


def list_input_devices() -> List[Dict[str, Any]]:
    """Return all available audio input devices."""
    devices = []
    if sd is None:
        return devices
    try:
        all_devs = sd.query_devices()
        for i, dev in enumerate(all_devs):
            max_ch = int(dev.get("max_input_channels", 0))
            if max_ch > 0:
                devices.append({
                    "index": i,
                    "name": dev["name"],
                    "hostapi": dev["hostapi"],
                    "max_input_channels": max_ch,
                    "channels": max_ch,
                    "default_samplerate": dev["default_samplerate"],
                })
    except Exception as e:
        logger.error(f"Error querying devices: {e}")
    return devices


def find_best_input_device(preferred_index: Optional[int] = None) -> Optional[int]:
    """Find the best matching audio input device."""
    devices = list_input_devices()
    if not devices:
        logger.warning("No input devices found on system!")
        return None

    if preferred_index is not None:
        for d in devices:
            if d["index"] == preferred_index:
                return preferred_index
        logger.warning(f"Preferred device index {preferred_index} not found in available input devices.")

    # Check for default device
    if sd is not None:
        try:
            default_dev = sd.default.device[0] if isinstance(sd.default.device, (list, tuple)) else sd.default.device
            if default_dev is not None and int(default_dev) >= 0:
                for d in devices:
                    if d["index"] == int(default_dev):
                        return int(default_dev)
        except Exception:
            pass

    # Priority 1: device with 'mic' or 'microphone' in name
    for d in devices:
        name_lower = d["name"].lower()
        if "microphone" in name_lower or "mic" in name_lower:
            return d["index"]

    # Priority 2: first available input device
    return devices[0]["index"]


class AudioRecorder:
    def __init__(
        self,
        device_index: Optional[int] = None,
        target_samplerate: int = 16000,
        level_callback: Optional[Callable[[float], None]] = None,
    ):
        self.device_index = device_index
        self.target_samplerate = target_samplerate
        self.level_callback = level_callback
        self.is_recording = False
        self._stream: Optional[Any] = None
        self._queue: queue.Queue = queue.Queue()
        self._actual_samplerate: int = target_samplerate
        self._actual_channels: int = 1
        self._lock = threading.Lock()

    def play_feedback_chime(self, chime_type: str = "start"):
        """Play subtle, pleasant audio feedback like Wispr Flow."""
        try:
            import winsound

            def _play():
                try:
                    if chime_type == "start":
                        winsound.Beep(980, 45)
                    elif chime_type == "done":
                        winsound.Beep(1200, 35)
                    elif chime_type == "cancel":
                        winsound.Beep(450, 60)
                except Exception:
                    pass

            threading.Thread(target=_play, daemon=True, name="ChimeThread").start()
        except Exception:
            pass

    def start_recording(self, device_index: Optional[int] = None) -> bool:
        """Alias for start() used by UI components."""
        return self.start(device_index=device_index)

    def stop_recording(self) -> Tuple[np.ndarray, int]:
        """Alias for stop() used by UI components."""
        return self.stop()

    def start(self, device_index: Optional[int] = None) -> bool:
        """Start recording from the audio input device."""
        with self._lock:
            if self.is_recording:
                logger.warning("Recording already in progress.")
                return True

            if sd is None:
                logger.error("sounddevice library is not available.")
                return False

            if device_index is not None:
                self.device_index = device_index

            resolved_device = find_best_input_device(self.device_index)
            if resolved_device is None:
                logger.error("No valid input device found.")
                return False

            self._queue = queue.Queue()

            try:
                dev_info = sd.query_devices(resolved_device)
            except Exception as e:
                logger.error(f"Failed to query device {resolved_device}: {e}")
                resolved_device = find_best_input_device(None)
                if resolved_device is None:
                    return False
                try:
                    dev_info = sd.query_devices(resolved_device)
                except Exception:
                    return False

            self.device_index = resolved_device
            logger.info(f"Using audio device [{resolved_device}]: {dev_info['name']}")

            max_ch = max(1, int(dev_info.get("max_input_channels", 1)))
            default_sr = int(dev_info.get("default_samplerate", 44100) or 44100)

            attempts = [
                (self.target_samplerate, 1),
                (default_sr, 1),
                (default_sr, min(max_ch, 2)),
                (48000, 1),
                (44100, 1),
                (48000, min(max_ch, 2)),
                (44100, min(max_ch, 2)),
            ]
            # Deduplicate while preserving order
            unique_attempts = list(dict.fromkeys(attempts))

            stream_opened = False
            for sr, ch in unique_attempts:
                if ch <= 0:
                    continue
                try:
                    def audio_callback(indata, frames, time_info, status):
                        if status:
                            logger.debug(f"Audio stream status: {status}")
                        if self.is_recording:
                            self._queue.put(indata.copy())
                        if self.level_callback:
                            try:
                                rms = float(np.sqrt(np.mean(np.square(indata, dtype=np.float32))))
                                self.level_callback(rms)
                            except Exception:
                                pass

                    stream = sd.InputStream(
                        device=resolved_device,
                        samplerate=sr,
                        channels=ch,
                        dtype="float32",
                        callback=audio_callback,
                    )
                    stream.start()
                    self._stream = stream
                    self._actual_samplerate = sr
                    self._actual_channels = ch
                    stream_opened = True
                    logger.info(f"Stream opened successfully with {sr}Hz, {ch}ch.")
                    break
                except Exception as e:
                    logger.debug(f"Failed stream open at {sr}Hz {ch}ch: {e}")
                    continue

            if not stream_opened:
                logger.error(f"Failed to open audio input stream on device {resolved_device}.")
                return False

            self.is_recording = True
            return True

    def stop(self) -> Tuple[np.ndarray, int]:
        """Stop recording and return (audio_data_16k_mono_float32, 16000)."""
        with self._lock:
            if not self.is_recording and self._stream is None:
                return np.array([], dtype=np.float32), self.target_samplerate

            self.is_recording = False
            stream = self._stream
            self._stream = None
            actual_sr = self._actual_samplerate

        if stream is not None:
            try:
                if hasattr(stream, "abort"):
                    stream.abort(ignore_errors=True)
                else:
                    stream.stop()
                stream.close(ignore_errors=True) if "ignore_errors" in stream.close.__code__.co_varnames else stream.close()
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")

        chunks = []
        while True:
            try:
                chunks.append(self._queue.get_nowait())
            except queue.Empty:
                break

        if not chunks:
            logger.warning("No audio frames collected.")
            return np.array([], dtype=np.float32), self.target_samplerate

        raw_audio = np.concatenate(chunks, axis=0)

        # Convert to mono
        if raw_audio.ndim > 1 and raw_audio.shape[1] > 1:
            mono_audio = raw_audio.mean(axis=1, dtype=np.float32)
        else:
            mono_audio = raw_audio.reshape(-1).astype(np.float32)

        if len(mono_audio) == 0:
            return np.array([], dtype=np.float32), self.target_samplerate

        # Resample to target_samplerate (16000Hz) using fast polyphase filtering
        if actual_sr != self.target_samplerate:
            gcd = int(np.gcd(self.target_samplerate, actual_sr))
            up = self.target_samplerate // gcd
            down = actual_sr // gcd
            mono_audio = scipy.signal.resample_poly(mono_audio, up, down).astype(np.float32)

        if len(mono_audio) == 0:
            return np.array([], dtype=np.float32), self.target_samplerate

        # Remove DC offset drift
        mono_audio = mono_audio - float(np.mean(mono_audio))

        # Peak normalize volume so Whisper always receives a clear, well-modulated signal
        max_val = float(np.max(np.abs(mono_audio)))
        if max_val > 0.005:
            mono_audio = (mono_audio / max_val) * 0.95

        # Clip values to [-1.0, 1.0]
        mono_audio = np.clip(mono_audio, -1.0, 1.0).astype(np.float32)
        logger.info(
            f"Captured {len(mono_audio)} samples ({len(mono_audio)/self.target_samplerate:.2f}s) "
            f"at {self.target_samplerate}Hz mono."
        )
        return mono_audio, self.target_samplerate

    @staticmethod
    def save_wav(filename: str | Path, audio_data: np.ndarray, samplerate: int = 16000) -> None:
        """Save float32 audio numpy array to 16-bit PCM WAV file."""
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        int16_data = (np.clip(audio_data, -1.0, 1.0) * 32767.0).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(samplerate)
            wf.writeframes(int16_data.tobytes())
        logger.info(f"Saved audio to {path} ({len(int16_data)} samples, {len(int16_data)/samplerate:.2f}s).")
