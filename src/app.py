import logging
import os
import sys
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QApplication

from src.audio import AudioRecorder
from src.cleanup import clean_transcript
from src.config import load_config, save_config
from src.hotkey import PushToTalkHotkeyListener
from src.injector import paste_text
from src.transcriber import WhisperTranscriber
from src.ui.history import HistoryDialog, add_history_entry
from src.ui.overlay import FloatingOverlay
from src.ui.settings import SettingsDialog
from src.ui.tray import WisprTrayIcon

logger = logging.getLogger("WisprClone.App")


class AppBridge(QObject):
    """Thread-safe Qt signal bridge for communication between background threads and the UI."""
    sig_recording_started = Signal()
    sig_recording_stopped = Signal()
    sig_transcription_started = Signal()
    sig_transcription_done = Signal(str)
    sig_error = Signal(str)


class WisprFlowApp:
    """Core application coordinator for Wispr Flow clone."""

    def __init__(self):
        self.config = load_config()
        self.bridge = AppBridge()

        # UI Components
        self.overlay = FloatingOverlay()

        # Audio recorder
        self.recorder = AudioRecorder(
            device_index=self.config.get("device_index"),
            level_callback=self.overlay.set_audio_level
        )

        # Local Whisper transcriber
        self.transcriber = WhisperTranscriber(
            model_size=self.config.get("model_size", "small")
        )
        self.tray = WisprTrayIcon(
            hotkey_str=self.config.get("hotkey", "ctrl+win"),
            on_toggle_recording=self.toggle_recording_manual,
            on_open_settings=self.open_settings,
            on_open_history=self.open_history,
            on_quit=self.quit_app
        )
        self.tray.show()

        self.settings_dialog: Optional[SettingsDialog] = None
        self.history_dialog: Optional[HistoryDialog] = None

        # Hotkey listener
        self.hotkey_listener = PushToTalkHotkeyListener(
            hotkey_str=self.config.get("hotkey", "ctrl+win"),
            on_start=self._on_hotkey_press,
            on_stop=self._on_hotkey_release
        )

        # Wire up bridge signals to UI methods
        self.bridge.sig_recording_started.connect(self._ui_on_recording_started)
        self.bridge.sig_recording_stopped.connect(self._ui_on_recording_stopped)
        self.bridge.sig_transcription_started.connect(self.overlay.show_transcribing)
        self.bridge.sig_transcription_done.connect(self._ui_on_transcription_done)

        self._manual_recording = False
        self._processing_lock = threading.Lock()

    def start(self):
        logger.info("Starting Wispr Flow Clone application...")
        self.hotkey_listener.start()

        # Warm up Whisper model in a background thread so first dictation has zero lag
        threading.Thread(target=self._warmup_model, daemon=True, name="ModelWarmup").start()

        self.tray.showMessage(
            "Vesper",
            f"Ready! Hold [{self.config.get('hotkey', 'ctrl+win').upper()}] anywhere to dictate.",
            self.tray.icon(),
            3000
        )

    def _warmup_model(self):
        try:
            logger.info("Warming up Whisper model in background...")
            self.transcriber.load_model()
            logger.info("Whisper model warmup completed.")
        except Exception as e:
            logger.error(f"Error during model warmup: {e}")

    def _on_hotkey_press(self):
        """Called by hotkey listener on background thread."""
        logger.info("Push-to-talk press detected.")
        self.bridge.sig_recording_started.emit()

    def _on_hotkey_release(self):
        """Called by hotkey listener on background thread."""
        logger.info("Push-to-talk release detected.")
        self.bridge.sig_recording_stopped.emit()

    def _ui_on_recording_started(self):
        """Qt Main Thread: update overlay and start mic stream."""
        if self.recorder.is_recording:
            return
        self.overlay.show_recording()
        self.tray.set_recording_state(True)
        if self.config.get("audio_feedback", True):
            self.recorder.play_feedback_chime("start")
        started = self.recorder.start(device_index=self.config.get("device_index"))
        if not started:
            self.overlay.hide_overlay()
            self.tray.set_recording_state(False)

    def _ui_on_recording_stopped(self):
        """Qt Main Thread: update overlay and trigger background transcription."""
        if not self.recorder.is_recording:
            return
        self.overlay.show_transcribing()
        self.tray.set_recording_state(False)

        # Offload transcription and injection to worker thread to prevent any UI freeze
        threading.Thread(
            target=self._process_audio_worker,
            daemon=True,
            name="AudioTranscriptionWorker"
        ).start()

    def _process_audio_worker(self):
        """Worker thread: stop recorder, transcribe audio, clean text, and paste into focused app."""
        with self._processing_lock:
            audio_data, sample_rate = self.recorder.stop()
            if len(audio_data) < int(sample_rate * 0.25):
                logger.info("Audio too short (<0.25s), skipping transcription.")
                self.bridge.sig_transcription_done.emit("")
                return

            try:
                # 1. Local Whisper Transcription / Translation
                raw_text = self.transcriber.transcribe(
                    audio_data,
                    language=self.config.get("language", "en"),
                    task=self.config.get("task", "transcribe"),
                    vad_filter=self.config.get("vad_filter", True)
                )

                if not raw_text:
                    logger.info("Transcription produced no speech.")
                    self.bridge.sig_transcription_done.emit("")
                    return

                # 2. Cleanup (fillers, spoken commands, punctuation, style)
                cleaned_text = clean_transcript(
                    raw_text,
                    cleanup_filler=self.config.get("cleanup_filler", True),
                    spoken_commands=self.config.get("spoken_commands", True),
                    style=self.config.get("style", "casual")
                )

                # 3. Add to History
                add_history_entry(cleaned_text, limit=self.config.get("history_limit", 20))

                # 4. Inject text into the focused application
                paste_text(cleaned_text, restore_clipboard=True)

                self.bridge.sig_transcription_done.emit(cleaned_text)
            except Exception as e:
                logger.error(f"Error in transcription pipeline: {e}", exc_info=True)
                self.bridge.sig_transcription_done.emit("")

    def _ui_on_transcription_done(self, text: str):
        """Qt Main Thread: show completion on overlay."""
        if text:
            self.overlay.show_done(preview_text=text)
            if self.config.get("audio_feedback", True):
                self.recorder.play_feedback_chime("done")
        else:
            self.overlay.hide_overlay()
            if self.config.get("audio_feedback", True):
                self.recorder.play_feedback_chime("cancel")

    def toggle_recording_manual(self):
        """Manual toggle from system tray menu."""
        if not self._manual_recording:
            self._manual_recording = True
            self._ui_on_recording_started()
        else:
            self._manual_recording = False
            self._ui_on_recording_stopped()

    def open_settings(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(on_saved=self._on_settings_saved)
        self.settings_dialog.show()
        self.settings_dialog.activateWindow()

    def _on_settings_saved(self, new_config: dict):
        self.config = new_config
        new_hotkey = new_config.get("hotkey", "ctrl+win")
        self.hotkey_listener.set_hotkey(new_hotkey)
        self.tray.update_hotkey(new_hotkey)

        new_model = new_config.get("model_size", "small")
        if new_model != self.transcriber.model_size:
            threading.Thread(
                target=lambda: self.transcriber.change_model(new_model),
                daemon=True
            ).start()

    def open_history(self):
        if self.history_dialog is None:
            self.history_dialog = HistoryDialog()
        self.history_dialog.refresh()
        self.history_dialog.show()
        self.history_dialog.activateWindow()

    def quit_app(self):
        logger.info("Quitting Wispr Flow Clone...")
        self.hotkey_listener.stop()
        if self.recorder.is_recording:
            self.recorder.stop()
        QApplication.quit()


def get_log_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "vesper.log"
    return Path(__file__).resolve().parent.parent / "vesper.log"


def main():
    log_file = get_log_file()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    wispr_app = WisprFlowApp()
    wispr_app.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
