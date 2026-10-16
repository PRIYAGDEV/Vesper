# -*- coding: utf-8 -*-
"""
FreeFlow - Settings & Preferences Dialog
Crafted with UI/UX Pro Max design intelligence:
- Deep obsidian card-based container layout (#0B0D14 / #131622)
- High-contrast typography hierarchy with Segoe UI Variable / Inter
- Interactive audio calibration VU meter with live decibel readout
- Clean visual toggles and segmented setting categories
"""

import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
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
    background-color: #0B0D14;
    color: #F8FAFC;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
}
QLabel {
    color: #94A3B8;
    font-size: 13px;
    font-weight: 500;
}
QLabel.sectionHeader {
    color: #F8FAFC;
    font-size: 14px;
    font-weight: 600;
}
QFrame.settingCard {
    background-color: #131622;
    border: 1px solid #1E2333;
    border-radius: 12px;
}
QLineEdit, QComboBox {
    background-color: #0E1019;
    color: #F8FAFC;
    border: 1px solid #252B3E;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #7C3AED;
    background-color: #121522;
}
QComboBox::drop-down {
    border: none;
    padding-right: 12px;
}
QComboBox QAbstractItemView {
    background-color: #131622;
    color: #F8FAFC;
    selection-background-color: #7C3AED;
    border: 1px solid #252B3E;
    border-radius: 8px;
    padding: 6px;
}
QCheckBox {
    color: #CBD5E1;
    font-size: 13px;
    spacing: 10px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #334155;
    background-color: #0E1019;
}
QCheckBox::indicator:hover {
    border: 1px solid #7C3AED;
}
QCheckBox::indicator:checked {
    background-color: #7C3AED;
    border: 1px solid #7C3AED;
}
QProgressBar {
    background-color: #0E1019;
    border: 1px solid #1E2333;
    border-radius: 5px;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #10B981, stop:0.65 #3B82F6, stop:0.85 #F59E0B, stop:1.0 #EF4444);
    border-radius: 4px;
}
QPushButton {
    background-color: #7C3AED;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #6D28D9;
}
QPushButton#cancelBtn {
    background-color: #1A1E2B;
    color: #94A3B8;
    border: 1px solid #252B3E;
}
QPushButton#cancelBtn:hover {
    background-color: #242A3C;
    color: #F8FAFC;
}
"""


class SettingsDialog(QDialog):
    """Ultra-modern, card-based preference panel for FreeFlow."""

    def __init__(self, parent=None, on_saved: Optional[Callable[[dict], None]] = None):
        super().__init__(parent)
        self.setWindowTitle("FreeFlow - Preferences")
        self.setFixedSize(540, 580)
        self.setStyleSheet(SETTINGS_STYLESHEET)
        self.on_saved = on_saved

        self.config = load_config()
        self._mic_monitor = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Title
        title_box = QHBoxLayout()
        title = QLabel("FreeFlow Preferences")
        title.setFont(QFont("Segoe UI Variable Display", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        title_box.addWidget(title)

        version_badge = QLabel("v1.0.0")
        version_badge.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.DemiBold))
        version_badge.setStyleSheet("""
            background-color: #1E2333;
            color: #A78BFA;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid #2E364F;
        """)
        title_box.addWidget(version_badge, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(title_box)

        # --- Card 1: Dictation & Model ---
        dictation_card = QFrame()
        dictation_card.setProperty("class", "settingCard")
        dictation_layout = QVBoxLayout(dictation_card)
        dictation_layout.setContentsMargins(16, 14, 16, 14)
        dictation_layout.setSpacing(10)

        card1_title = QLabel("Dictation Engine")
        card1_title.setProperty("class", "sectionHeader")
        dictation_layout.addWidget(card1_title)

        d_form = QFormLayout()
        d_form.setSpacing(10)
        d_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Push-to-Talk Hotkey
        self.hotkey_input = QLineEdit(self.config.get("hotkey", "ctrl+win"))
        self.hotkey_input.setPlaceholderText("e.g. ctrl+win, ctrl+space, alt+space")
        d_form.addRow("Push-to-Talk Hotkey:", self.hotkey_input)

        # Whisper Model
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
        d_form.addRow("Whisper Model:", self.model_combo)

        # Writing Style (Wispr Flow signature feature)
        self.style_combo = QComboBox()
        self.style_combo.addItem("Casual (Conversational, filler words removed)", "casual")
        self.style_combo.addItem("Professional (Polished corporate tone)", "professional")
        self.style_combo.addItem("Bullet Points (Formats speech into markdown lists)", "bullet_points")
        self.style_combo.addItem("Developer / Code (Formats camelCase & snake_case)", "code")
        curr_style = self.config.get("style", "casual")
        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == curr_style:
                self.style_combo.setCurrentIndex(i)
                break
        d_form.addRow("Writing Style:", self.style_combo)

        dictation_layout.addLayout(d_form)
        main_layout.addWidget(dictation_card)

        # --- Card 2: Audio & Microphone Calibration ---
        audio_card = QFrame()
        audio_card.setProperty("class", "settingCard")
        audio_layout = QVBoxLayout(audio_card)
        audio_layout.setContentsMargins(16, 14, 16, 14)
        audio_layout.setSpacing(10)

        card2_title = QLabel("Microphone & Calibration")
        card2_title.setProperty("class", "sectionHeader")
        audio_layout.addWidget(card2_title)

        a_form = QFormLayout()
        a_form.setSpacing(10)
        a_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.device_combo = QComboBox()
        self.device_combo.addItem("Default System Microphone", None)
        devices = list_input_devices()
        curr_dev = self.config.get("device_index")
        dev_selected_idx = 0
        for i, dev in enumerate(devices, start=1):
            name = dev["name"]
            if len(name) > 38:
                name = name[:36] + "..."
            self.device_combo.addItem(f"{name} (ch={dev['channels']})", dev["index"])
            if dev["index"] == curr_dev:
                dev_selected_idx = i
        self.device_combo.setCurrentIndex(dev_selected_idx)
        self.device_combo.currentIndexChanged.connect(self._restart_mic_monitor)
        a_form.addRow("Input Device:", self.device_combo)

        # Live VU Audio Level Meter
        self.meter_bar = QProgressBar()
        self.meter_bar.setRange(0, 100)
        self.meter_bar.setValue(0)
        self.meter_bar.setTextVisible(False)
        a_form.addRow("Live Mic Level:", self.meter_bar)

        audio_layout.addLayout(a_form)
        main_layout.addWidget(audio_card)

        # --- Card 3: Enhancements & Toggles ---
        toggles_card = QFrame()
        toggles_card.setProperty("class", "settingCard")
        toggles_layout = QVBoxLayout(toggles_card)
        toggles_layout.setContentsMargins(16, 14, 16, 14)
        toggles_layout.setSpacing(8)

        card3_title = QLabel("AI Enhancements & Audio Feedback")
        card3_title.setProperty("class", "sectionHeader")
        toggles_layout.addWidget(card3_title)

        tog_row1 = QHBoxLayout()
        self.cleanup_check = QCheckBox("Remove hesitation fillers ('um', 'uh', 'like')")
        self.cleanup_check.setChecked(self.config.get("cleanup_filler", True))
        tog_row1.addWidget(self.cleanup_check)

        self.commands_check = QCheckBox("Spoken commands ('new line', 'comma')")
        self.commands_check.setChecked(self.config.get("spoken_commands", True))
        tog_row1.addWidget(self.commands_check)
        toggles_layout.addLayout(tog_row1)

        tog_row2 = QHBoxLayout()
        self.chimes_check = QCheckBox("Sound chimes (Start / Done feedback)")
        self.chimes_check.setChecked(self.config.get("audio_feedback", True))
        tog_row2.addWidget(self.chimes_check)

        self.vad_check = QCheckBox("Silero Voice Activity Detection (VAD)")
        self.vad_check.setChecked(self.config.get("vad_filter", True))
        tog_row2.addWidget(self.vad_check)
        toggles_layout.addLayout(tog_row2)

        main_layout.addWidget(toggles_card)

        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Preferences")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

        # Start live VU meter
        self._start_mic_monitor()

    def _start_mic_monitor(self):
        self._stop_mic_monitor()
        dev_idx = self.device_combo.currentData()
        try:
            self._mic_monitor = AudioRecorder(
                device_index=dev_idx,
                level_callback=self._on_mic_level
            )
            self._mic_monitor.start_recording()
        except Exception as e:
            logger.warning(f"Could not start mic meter: {e}")

    def _stop_mic_monitor(self):
        if self._mic_monitor:
            try:
                self._mic_monitor.stop_recording()
            except Exception:
                pass
            self._mic_monitor = None

    def _restart_mic_monitor(self):
        self._start_mic_monitor()

    def _on_mic_level(self, level: float):
        # Scale logarithmically for responsive dB-like deflection
        val = int(min(100, (level ** 0.5) * 220))
        self.meter_bar.setValue(val)

    def done(self, r):
        self._stop_mic_monitor()
        super().done(r)

    def _save_settings(self):
        new_hotkey = self.hotkey_input.text().strip().lower() or "ctrl+win"
        new_model = self.model_combo.currentData()
        new_style = self.style_combo.currentData()
        new_device = self.device_combo.currentData()
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

        self._stop_mic_monitor()
        self.accept()
