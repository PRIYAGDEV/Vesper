import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.audio import list_input_devices, AudioRecorder
from src.config import load_config, save_config

logger = logging.getLogger("WisprClone.Settings")

SETTINGS_STYLESHEET = """
QDialog {
    background-color: #0F1015;
    color: #F3F4F6;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
QLabel {
    color: #E2E8F0;
    font-size: 13px;
    font-weight: 500;
}
QLineEdit, QComboBox {
    background-color: #1A1C24;
    color: #FFFFFF;
    border: 1px solid #2E3346;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #8B5CF6;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #8B5CF6;
    background-color: #212430;
}
QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #1A1C24;
    color: #FFFFFF;
    selection-background-color: #7C3AED;
    border: 1px solid #2E3346;
    border-radius: 6px;
    padding: 4px;
}
QCheckBox {
    color: #E2E8F0;
    font-size: 13px;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #475569;
    background-color: #1A1C24;
}
QCheckBox::indicator:checked {
    background-color: #8B5CF6;
    border: 1px solid #8B5CF6;
}
QProgressBar {
    background-color: #1A1C24;
    border: 1px solid #2E3346;
    border-radius: 5px;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:0.7 #8B5CF6, stop:1 #EC4899);
    border-radius: 4px;
}
QPushButton {
    background-color: #7C3AED;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #6D28D9;
}
QPushButton#cancelBtn {
    background-color: #262936;
    color: #E2E8F0;
}
QPushButton#cancelBtn:hover {
    background-color: #333748;
}
"""


class SettingsDialog(QDialog):
    """Ultra-modern settings dialog replicating Wispr Flow's preference panel."""

    def __init__(self, parent=None, on_saved: Optional[Callable[[dict], None]] = None):
        super().__init__(parent)
        self.setWindowTitle("FreeFlow - Settings")
        self.setFixedSize(520, 520)
        self.setStyleSheet(SETTINGS_STYLESHEET)
        self.on_saved = on_saved

        self.config = load_config()
        self._mic_monitor = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        title = QLabel("FreeFlow Preferences")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 2px;")
        main_layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # 1. Dictation Mode / Language (English only)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("English (Speak English -> Types English)", "en_direct")
        self.mode_combo.setCurrentIndex(0)
        form.addRow("Language:", self.mode_combo)

        # 2. Writing Style (Signature Wispr Flow feature)
        self.style_combo = QComboBox()
        self.style_combo.addItem("Casual (Conversational, filler words removed)", "casual")
        self.style_combo.addItem("Professional (Polished business tone & punctuation)", "professional")
        self.style_combo.addItem("Bullet Points (Automatically formats lists)", "bullet_points")
        self.style_combo.addItem("Developer / Code (Formats camelCase, snake_case)", "code")
        curr_style = self.config.get("style", "casual")
        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == curr_style:
                self.style_combo.setCurrentIndex(i)
                break
        form.addRow("Writing Style:", self.style_combo)

        # 3. Push-to-Talk Hotkey
        self.hotkey_input = QLineEdit(self.config.get("hotkey", "ctrl+win"))
        self.hotkey_input.setPlaceholderText("e.g. ctrl+win, ctrl+space, alt+space")
        form.addRow("Push-to-Talk Hotkey:", self.hotkey_input)

        # 4. Whisper Model
        self.model_combo = QComboBox()
        models = [
            ("small (Recommended - 3x High Accuracy, ~460MB)", "small"),
            ("base (Multilingual - Fast, ~145MB)", "base"),
            ("tiny (Multilingual - Minimal, ~75MB)", "tiny"),
        ]
        curr_model = self.config.get("model_size", "small")
        selected_idx = 0
        for i, (label, val) in enumerate(models):
            self.model_combo.addItem(label, val)
            if val == curr_model:
                selected_idx = i
        self.model_combo.setCurrentIndex(selected_idx)
        form.addRow("Whisper Model:", self.model_combo)

        # 5. Microphone Selector
        self.device_combo = QComboBox()
        self.device_combo.addItem("Default System Microphone", None)
        devices = list_input_devices()
        curr_dev = self.config.get("device_index")
        dev_selected_idx = 0
        for i, d in enumerate(devices):
            label = f"[{d['index']}] {d['name'][:34]}"
            self.device_combo.addItem(label, d["index"])
            if curr_dev is not None and d["index"] == curr_dev:
                dev_selected_idx = i + 1
        self.device_combo.setCurrentIndex(dev_selected_idx)
        form.addRow("Microphone Device:", self.device_combo)

        # 6. Live Mic Volume Meter
        self.mic_meter = QProgressBar()
        self.mic_meter.setRange(0, 100)
        self.mic_meter.setValue(0)
        self.mic_meter.setTextVisible(False)
        form.addRow("Mic Input Level:", self.mic_meter)

        main_layout.addLayout(form)

        # Toggles
        toggles_layout = QVBoxLayout()
        toggles_layout.setSpacing(8)

        self.cleanup_check = QCheckBox("Remove filler words (um, uh, you know, like)")
        self.cleanup_check.setChecked(self.config.get("cleanup_filler", True))
        toggles_layout.addWidget(self.cleanup_check)

        self.commands_check = QCheckBox("Enable spoken punctuation (new line, period, comma, quote)")
        self.commands_check.setChecked(self.config.get("spoken_commands", True))
        toggles_layout.addWidget(self.commands_check)

        self.chimes_check = QCheckBox("Play audio feedback chimes on start and finish")
        self.chimes_check.setChecked(self.config.get("audio_feedback", True))
        toggles_layout.addWidget(self.chimes_check)

        self.vad_check = QCheckBox("Voice Activity Detection (auto-trim silence with Silero VAD)")
        self.vad_check.setChecked(self.config.get("vad_filter", True))
        toggles_layout.addWidget(self.vad_check)

        main_layout.addLayout(toggles_layout)
        main_layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save & Apply")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

        # Start live microphone monitoring for testing volume
        self._start_mic_meter()

    def _start_mic_meter(self):
        try:
            self._mic_recorder = AudioRecorder(
                device_index=self.config.get("device_index"),
                level_callback=self._on_live_mic_level
            )
            self._mic_recorder.start()
        except Exception as e:
            logger.debug(f"Could not start mic test meter: {e}")

    def _on_live_mic_level(self, level: float):
        pct = min(100, int(level * 400))
        QTimer.singleShot(0, lambda: self.mic_meter.setValue(pct))

    def done(self, r):
        if hasattr(self, "_mic_recorder") and self._mic_recorder:
            try:
                self._mic_recorder.stop()
            except Exception:
                pass
        super().done(r)

    def closeEvent(self, event):
        if hasattr(self, "_mic_recorder") and self._mic_recorder:
            try:
                self._mic_recorder.stop()
            except Exception:
                pass
        super().closeEvent(event)

    def _save_settings(self):
        new_hotkey = self.hotkey_input.text().strip().lower() or "ctrl+win"
        new_model = self.model_combo.currentData()
        new_style = self.style_combo.currentData()
        new_device = self.device_combo.currentData()
        # Enforce English-to-English dictation
        new_lang = "en"
        new_task = "transcribe"

        self.config["hotkey"] = new_hotkey
        self.config["model_size"] = new_model
        self.config["style"] = new_style
        self.config["device_index"] = new_device
        self.config["language"] = new_lang
        self.config["task"] = new_task
        self.config["cleanup_filler"] = self.cleanup_check.isChecked()
        self.config["spoken_commands"] = self.commands_check.isChecked()
        self.config["audio_feedback"] = self.chimes_check.isChecked()
        self.config["vad_filter"] = self.vad_check.isChecked()

        save_config(self.config)
        logger.info(f"Settings saved: {self.config}")

        if self.on_saved:
            self.on_saved(self.config)

        self.accept()
