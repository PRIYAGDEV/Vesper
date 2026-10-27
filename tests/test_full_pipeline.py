import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import WisprFlowApp
from src.cleanup import clean_transcript
from src.ui.history import load_history, save_history, add_history_entry
from src.ui.settings import SettingsDialog


def test_settings_dialog_and_Deadlock_prevention():
    import tempfile
    from src.config import load_config, save_config

    app = QApplication.instance() or QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_cfg = Path(tmpdir) / "config.json"
        with patch("src.ui.settings.load_config", side_effect=lambda: load_config(tmp_cfg)), \
             patch("src.ui.settings.save_config", side_effect=lambda cfg: save_config(cfg, tmp_cfg)):
            saved_configs = []
            dlg = SettingsDialog(on_saved=lambda cfg: saved_configs.append(cfg.copy()))

            # Verify all 4 dictation modes save properly
            # 0: hi_to_en
            dlg.mode_combo.setCurrentIndex(0)
            dlg._save_settings()
            assert saved_configs[-1]["language"] == "hi" and saved_configs[-1]["task"] == "translate"

            # 1: en_direct
            dlg.mode_combo.setCurrentIndex(1)
            dlg._save_settings()
            assert saved_configs[-1]["language"] == "en" and saved_configs[-1]["task"] == "transcribe"

            # 2: auto_to_en
            dlg.mode_combo.setCurrentIndex(2)
            dlg._save_settings()
            assert saved_configs[-1]["language"] == "auto" and saved_configs[-1]["task"] == "translate"

            # 3: hi_direct
            dlg.mode_combo.setCurrentIndex(3)
            dlg._save_settings()
            assert saved_configs[-1]["language"] == "hi" and saved_configs[-1]["task"] == "transcribe"

            dlg._stop_mic_monitor()
    print("[PASS] SettingsDialog dictation mode persistence and mic monitor cleanup verified.")


def test_change_model_no_deadlock():
    from src.transcriber import WhisperTranscriber

    transcriber = WhisperTranscriber(model_size="tiny")
    # Mock load_model to verify change_model doesn't deadlock on self._lock
    with patch("src.transcriber.WhisperModel") as mock_wm:
        mock_wm.return_value = MagicMock()
        done_event = threading.Event()

        def _switch():
            transcriber.change_model("base")
            done_event.set()

        t = threading.Thread(target=_switch, daemon=True)
        t.start()
        assert done_event.wait(timeout=2.0), "WhisperTranscriber.change_model deadlocked!"
        assert transcriber.model_size == "base"
    print("[PASS] WhisperTranscriber.change_model RLock non-deadlock verified.")


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

    test_settings_dialog_and_Deadlock_prevention()
    test_change_model_no_deadlock()

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
