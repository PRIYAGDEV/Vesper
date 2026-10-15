import sys
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import WisprFlowApp
from src.cleanup import clean_transcript
from src.ui.history import load_history, save_history, add_history_entry


def test_full_pipeline():
    print("Initializing Qt Application...")
    app = QApplication.instance() or QApplication(sys.argv)

    print("Instantiating WisprFlowApp...")
    wispr = WisprFlowApp()
    assert wispr.overlay is not None, "Overlay should be created"
    assert wispr.tray is not None, "Tray should be created"
    assert wispr.hotkey_listener is not None, "Hotkey listener should be created"
    print("[PASS] UI and controller components initialized.")

    # Test overlay state transitions
    wispr.overlay.show_recording()
    assert wispr.overlay.state == "recording"
    wispr.overlay.show_transcribing()
    assert wispr.overlay.state == "transcribing"
    wispr.overlay.show_done("Testing preview text")
    assert wispr.overlay.state == "done"
    wispr.overlay.hide_overlay()
    print("[PASS] Floating overlay state transitions passed.")

    # Test transcription and cleanup integration
    test_wav = Path("tests/hello_world.wav")
    assert test_wav.exists()
    raw_text = wispr.transcriber.transcribe(test_wav, language="en", vad_filter=True)
    print(f"Raw transcription: '{raw_text}'")
    assert len(raw_text) > 0

    cleaned = clean_transcript(raw_text, cleanup_filler=True, spoken_commands=True)
    print(f"Cleaned transcription: '{cleaned}'")

    # Test history insertion
    add_history_entry(cleaned, limit=20)
    history = load_history()
    assert len(history) > 0
    assert history[0]["text"] == cleaned
    print("[PASS] History insertion verified.")

    # Clean shutdown
    wispr.hotkey_listener.stop()
    print("\nALL FULL PIPELINE TESTS PASSED!")


if __name__ == "__main__":
    test_full_pipeline()
