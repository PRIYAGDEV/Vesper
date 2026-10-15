import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.config import load_config
from src.audio import AudioRecorder, list_input_devices
from src.hotkey import PushToTalkHotkeyListener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("WisprClone.Step1")


def main():
    print("=" * 60)
    print(" Wispr Flow Clone - Step 1: Push-to-Talk Audio Recorder")
    print("=" * 60)

    config = load_config()
    hotkey = config.get("hotkey", "ctrl+win")
    output_wav = Path("test_recording.wav")

    print("\nDetecting audio input devices:")
    devices = list_input_devices()
    for d in devices:
        print(f"  [{d['index']}] {d['name']} (Channels: {d['max_input_channels']}, Rate: {d['default_samplerate']}Hz)")

    recorder = AudioRecorder(device_index=config.get("device_index"))
    record_count = 0

    def on_recording_start():
        nonlocal record_count
        print(f"\n[MIC ACTIVE] >>> RECORDING STARTED (Hold {hotkey})...")
        recorder.start()

    def on_recording_stop():
        nonlocal record_count
        print("[MIC STOPPED] <<< RECORDING STOPPED. Processing audio...")
        audio_data, sample_rate = recorder.stop()
        if len(audio_data) > 0:
            record_count += 1
            filename = f"test_recording_{record_count}.wav" if record_count > 1 else str(output_wav)
            recorder.save_wav(filename, audio_data, sample_rate)
            duration = len(audio_data) / sample_rate
            print(f"[SUCCESS] Saved {duration:.2f}s of audio to: {filename}")
            print(f"[READY] Ready for next recording or press Ctrl+C in this console to exit.\n")
        else:
            print("[WARNING] No audio captured (too short or silent).\n")

    listener = PushToTalkHotkeyListener(
        hotkey_str=hotkey,
        on_start=on_recording_start,
        on_stop=on_recording_stop
    )
    listener.start()

    print(f"\n>>> HOTKEY ACTIVE: [{hotkey.upper()}]")
    print(f"Hold [{hotkey.upper()}] and speak into your microphone.")
    print(f"Release [{hotkey.upper()}] to stop and save audio to '{output_wav}'.")
    print("Press Ctrl+C in this terminal to quit.\n")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nExiting Step 1 test.")
    finally:
        listener.stop()


if __name__ == "__main__":
    main()
