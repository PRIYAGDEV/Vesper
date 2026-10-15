import os
import sys
import time
import wave
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.audio import AudioRecorder, list_input_devices, find_best_input_device


def test_list_devices():
    devices = list_input_devices()
    print(f"Found {len(devices)} input devices.")
    assert isinstance(devices, list)
    return devices


def test_record_and_save():
    dev = find_best_input_device()
    print(f"Testing AudioRecorder with device: {dev}")
    recorder = AudioRecorder(device_index=dev)

    started = recorder.start()
    assert started, "Recorder failed to start"
    assert recorder.is_recording, "is_recording should be True"

    print("Recording for 1.2 seconds...")
    time.sleep(1.2)

    audio_data, sample_rate = recorder.stop()
    assert not recorder.is_recording, "is_recording should be False"
    assert sample_rate == 16000, f"Expected 16000 sample rate, got {sample_rate}"
    assert isinstance(audio_data, np.ndarray), "Audio data must be numpy array"
    assert audio_data.dtype == np.float32, f"Audio dtype must be float32, got {audio_data.dtype}"
    assert len(audio_data) > 0, "Audio data is empty"

    duration = len(audio_data) / sample_rate
    print(f"Recorded {len(audio_data)} samples ({duration:.2f} seconds)")

    test_wav = Path("tests/output_test.wav")
    recorder.save_wav(test_wav, audio_data, sample_rate)

    assert test_wav.exists(), "Output WAV was not created"
    assert test_wav.stat().st_size > 44, "Output WAV file is too small or missing header"

    with wave.open(str(test_wav), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        print(f"WAV validation: {channels}ch, {sampwidth*8}-bit, {framerate}Hz, {nframes} frames")
        assert channels == 1, f"Expected 1 channel, got {channels}"
        assert sampwidth == 2, f"Expected 16-bit (2 bytes), got {sampwidth}"
        assert framerate == 16000, f"Expected 16000Hz, got {framerate}"
        assert nframes > 0, "No frames in WAV"

    print("ALL AUDIO RECORDING TESTS PASSED!")


if __name__ == "__main__":
    test_list_devices()
    test_record_and_save()
