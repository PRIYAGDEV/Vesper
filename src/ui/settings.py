# -*- coding: utf-8 -*-
"""
Vesper - Settings & Preferences Dialog
Crafted with UI/UX Pro Max design intelligence:
- Deep obsidian card-based container layout (#090B11 / #121521)
- Interactive Push-to-Talk Hotkey Recorder button + quick preset chips
- Live audio calibration VU meter with dB readout & signal health badge
- Custom animated toggle switches and clean typography with zero text clipping
"""

import logging
import math
from typing import Callable, List, Optional

from PySide6.QtCore import Qt, QRectF, QSize, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QKeyEvent, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
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
    background-color: #090B11;
    color: #F8FAFC;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
}
QLabel {
    color: #94A3B8;
    font-size: 13px;
    font-weight: 500;
}
QLabel.formLabel {
    color: #CBD5E1;
    font-size: 13px;
    font-weight: 600;
    min-width: 118px;
}
QLabel.sectionHeader {
    color: #F8FAFC;
    font-size: 14px;
    font-weight: 700;
}
QLabel.sectionSub {
    color: #64748B;
    font-size: 12px;
    font-weight: 400;
}
QFrame.settingCard {
    background-color: #121521;
    border: 1px solid #1E2438;
    border-radius: 12px;
}
QLineEdit, QComboBox {
    background-color: #0B0E17;
    color: #F8FAFC;
    border: 1px solid #252D44;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:hover, QComboBox:hover {
    border: 1px solid #3B466B;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #7C3AED;
    background-color: #101422;
}
QComboBox::drop-down {
    border: none;
    padding-right: 12px;
}
QComboBox QAbstractItemView {
    background-color: #121521;
    color: #F8FAFC;
    selection-background-color: #7C3AED;
    border: 1px solid #2A324B;
    border-radius: 8px;
    padding: 6px;
}
QProgressBar {
    background-color: #0B0E17;
    border: 1px solid #1E2438;
    border-radius: 5px;
    height: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #10B981, stop:0.60 #3B82F6, stop:0.82 #F59E0B, stop:1.0 #EF4444);
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
    background-color: #161A29;
    color: #94A3B8;
    border: 1px solid #232A40;
}
QPushButton#cancelBtn:hover {
    background-color: #1F2538;
    color: #F8FAFC;
}
QPushButton#recordKeyBtn {
    background-color: #1A1F33;
    color: #C4B5FD;
    border: 1px solid #313B59;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#recordKeyBtn:hover {
    background-color: #252C47;
    border: 1px solid #7C3AED;
    color: #FFFFFF;
}
QPushButton#recordKeyBtn[recording="true"] {
    background-color: #3B1222;
    color: #FCA5A5;
    border: 1px solid #EF4444;
}
QPushButton.presetChip {
    background-color: #151A2B;
    color: #94A3B8;
    border: 1px solid #242C46;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton.presetChip:hover {
    background-color: #1E253B;
    color: #F8FAFC;
    border: 1px solid #6366F1;
}
"""


class BrandAvatar(QWidget):
    """Custom vector brand emblem for the Preferences header."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(38, 38)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, 38, 38)
        grad.setColorAt(0.0, QColor(139, 92, 246))
        grad.setColorAt(1.0, QColor(79, 70, 229))

        path = QPainterPath()
        path.addRoundedRect(QRectF(1, 1, 36, 36), 10, 10)
        painter.fillPath(path, QBrush(grad))

        painter.setPen(QPen(QColor(255, 255, 255, 55), 1.0))
        painter.drawPath(path)

        bars = [9, 17, 23, 15, 10]
        bar_w = 2.7
        spacing = 2.7
        total_w = len(bars) * bar_w + (len(bars) - 1) * spacing
        start_x = (38.0 - total_w) / 2.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 245))
        for i, bh in enumerate(bars):
            bx = start_x + i * (bar_w + spacing)
            by = (38.0 - bh) / 2.0
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bh), 1.35, 1.35)


class ToggleSwitch(QCheckBox):
    """Modern pill-shaped iOS/macOS style toggle switch with title and subtitle."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(28)

    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        return QSize(46 + 10 + fm.horizontalAdvance(self.text()) + 8, 28)

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        sw_w = 38.0
        sw_h = 20.0
        sw_y = (self.height() - sw_h) / 2.0
        sw_rect = QRectF(0.0, sw_y, sw_w, sw_h)

        checked = self.isChecked()
        if checked:
            track_grad = QLinearGradient(0, sw_y, sw_w, sw_y + sw_h)
            track_grad.setColorAt(0.0, QColor(139, 92, 246))
            track_grad.setColorAt(1.0, QColor(109, 40, 217))
            painter.setBrush(QBrush(track_grad))
            painter.setPen(QPen(QColor(167, 139, 250, 90), 1.0))
        else:
            painter.setBrush(QColor(22, 27, 43))
            painter.setPen(QPen(QColor(51, 65, 85), 1.0))

        painter.drawRoundedRect(sw_rect, sw_h / 2.0, sw_h / 2.0)

        # Thumb circle
        thumb_r = 7.0
        thumb_x = (sw_w - thumb_r * 2 - 3.0) if checked else 3.0
        thumb_y = sw_y + (sw_h - thumb_r * 2) / 2.0
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255) if checked else QColor(148, 163, 184))
        painter.drawEllipse(QRectF(thumb_x, thumb_y, thumb_r * 2, thumb_r * 2))

        # Label text
        font = QFont("Segoe UI Variable Text", 10, QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(241, 245, 249) if checked else QColor(148, 163, 184))
        text_rect = QRectF(sw_w + 10.0, 0.0, self.width() - sw_w - 10.0, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class SettingsDialog(QDialog):
    """Ultra-modern, card-based preference panel for Vesper."""

    sig_mic_level = Signal(float)

    def __init__(self, parent=None, on_saved: Optional[Callable[[dict], None]] = None):
        super().__init__(parent)
        self.setWindowTitle("Vesper — Preferences")
        self.setMinimumSize(640, 680)
        self.resize(640, 680)
        self.setStyleSheet(SETTINGS_STYLESHEET)
        self.on_saved = on_saved

        self.config = load_config()
        self._mic_monitor: Optional[AudioRecorder] = None
        self._recording_hotkey = False
        self._captured_keys: List[str] = []
        self.sig_mic_level.connect(self._update_meter_bar)
        self._init_ui()

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", "formLabel")
        return lbl

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # --- Top Brand Header ---
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        avatar = BrandAvatar()
        header_row.addWidget(avatar)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("Vesper Preferences")
        title.setFont(QFont("Segoe UI Variable Display", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        title_col.addWidget(title)

        subtitle = QLabel("100% Local AI Voice Dictation & Translation Engine")
        subtitle.setProperty("class", "sectionSub")
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        version_badge = QLabel("v1.1.0 • Local AI")
        version_badge.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.DemiBold))
        version_badge.setStyleSheet("""
            background-color: #171B2E;
            color: #A78BFA;
            padding: 4px 10px;
            border-radius: 7px;
            border: 1px solid #2A3252;
        """)
        header_row.addWidget(version_badge, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addLayout(header_row)

        # --- Card 1: Dictation & Model ---
        dictation_card = QFrame()
        dictation_card.setProperty("class", "settingCard")
        dictation_layout = QVBoxLayout(dictation_card)
        dictation_layout.setContentsMargins(18, 15, 18, 15)
        dictation_layout.setSpacing(11)

        card1_title = QLabel("Dictation & Language Engine")
        card1_title.setProperty("class", "sectionHeader")
        dictation_layout.addWidget(card1_title)

        d_form = QFormLayout()
        d_form.setSpacing(10)
        d_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        d_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Dictation Mode / Language
        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumWidth(420)
        self.mode_combo.addItem("Hindi to English (Speak Hindi → Types English)", "hi_to_en")
        self.mode_combo.addItem("English Dictation (Speak English → Types English)", "en_direct")
        self.mode_combo.addItem("Auto-Detect Language → Translate to English", "auto_to_en")
        self.mode_combo.addItem("Hindi Dictation (Speak Hindi → Types Devanagari)", "hi_direct")
        curr_task = self.config.get("task", "translate")
        curr_lang = self.config.get("language", "hi")
        if curr_task == "translate" and curr_lang == "hi":
            self.mode_combo.setCurrentIndex(0)
        elif curr_task == "transcribe" and curr_lang == "en":
            self.mode_combo.setCurrentIndex(1)
        elif curr_task == "translate" and curr_lang in ("auto", None):
            self.mode_combo.setCurrentIndex(2)
        elif curr_task == "transcribe" and curr_lang == "hi":
            self.mode_combo.setCurrentIndex(3)
        else:
            self.mode_combo.setCurrentIndex(0)
        d_form.addRow(self._make_label("Dictation Mode:"), self.mode_combo)

        # Push-to-Talk Hotkey with interactive Recorder + Preset chips
        hotkey_widget = QWidget()
        hotkey_container = QVBoxLayout(hotkey_widget)
        hotkey_container.setContentsMargins(0, 0, 0, 0)
        hotkey_container.setSpacing(6)

        hotkey_row = QHBoxLayout()
        hotkey_row.setContentsMargins(0, 0, 0, 0)
        hotkey_row.setSpacing(8)
        self.hotkey_input = QLineEdit(self.config.get("hotkey", "ctrl+win"))
        self.hotkey_input.setMinimumHeight(34)
        self.hotkey_input.setPlaceholderText("e.g. ctrl+win, ctrl+space, alt+space")
        hotkey_row.addWidget(self.hotkey_input, stretch=1)

        self.record_key_btn = QPushButton("Record Shortcut")
        self.record_key_btn.setObjectName("recordKeyBtn")
        self.record_key_btn.setMinimumHeight(34)
        self.record_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_key_btn.clicked.connect(self._toggle_hotkey_recorder)
        hotkey_row.addWidget(self.record_key_btn)
        hotkey_container.addLayout(hotkey_row)

        presets_row = QHBoxLayout()
        presets_row.setContentsMargins(0, 0, 0, 0)
        presets_row.setSpacing(6)
        presets_lbl = QLabel("Quick Presets:")
        presets_lbl.setStyleSheet("color: #64748B; font-size: 11.5px;")
        presets_row.addWidget(presets_lbl)

        for label, hk in [("Ctrl + Win", "ctrl+win"), ("Ctrl + Space", "ctrl+space"), ("Alt + Space", "alt+space"), ("F8", "f8")]:
            chip = QPushButton(label)
            chip.setProperty("class", "presetChip")
            chip.setFixedHeight(24)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda checked=False, val=hk: self._set_hotkey_preset(val))
            presets_row.addWidget(chip)
        presets_row.addStretch()
        hotkey_container.addLayout(presets_row)

        d_form.addRow(self._make_label("Push-to-Talk:"), hotkey_widget)

        # Whisper Model
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(420)
        models = [
            ("Small — High Accuracy Multilingual (~460 MB)", "small"),
            ("Base — Fast Balanced Multilingual (~145 MB)", "base"),
            ("Tiny — Ultra-Fast Lightweight (~75 MB)", "tiny"),
        ]
        curr_model = self.config.get("model_size", "small")
        selected_idx = 0
        for i, (label, val) in enumerate(models):
            self.model_combo.addItem(label, val)
            if val == curr_model:
                selected_idx = i
        self.model_combo.setCurrentIndex(selected_idx)
        d_form.addRow(self._make_label("Whisper Model:"), self.model_combo)

        # Writing Style (Wispr Flow signature feature)
        self.style_combo = QComboBox()
        self.style_combo.setMinimumWidth(420)
        self.style_combo.addItem("Casual — Conversational, fillers removed", "casual")
        self.style_combo.addItem("Professional — Polished corporate tone", "professional")
        self.style_combo.addItem("Bullet Points — Formats speech into lists", "bullet_points")
        self.style_combo.addItem("Developer / Code — Formats camelCase & snake_case", "code")
        curr_style = self.config.get("style", "casual")
        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == curr_style:
                self.style_combo.setCurrentIndex(i)
                break
        d_form.addRow(self._make_label("Writing Style:"), self.style_combo)

        dictation_layout.addLayout(d_form)
        main_layout.addWidget(dictation_card)

        # --- Card 2: Audio & Microphone Calibration ---
        audio_card = QFrame()
        audio_card.setProperty("class", "settingCard")
        audio_layout = QVBoxLayout(audio_card)
        audio_layout.setContentsMargins(18, 15, 18, 15)
        audio_layout.setSpacing(10)

        audio_hdr = QHBoxLayout()
        card2_title = QLabel("Microphone & Live Calibration")
        card2_title.setProperty("class", "sectionHeader")
        audio_hdr.addWidget(card2_title)
        audio_hdr.addStretch()

        self.mic_status_label = QLabel("● Ready")
        self.mic_status_label.setStyleSheet("""
            background-color: #112220;
            color: #34D399;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 9px;
            border-radius: 6px;
            border: 1px solid #1E3A34;
        """)
        audio_hdr.addWidget(self.mic_status_label)
        audio_layout.addLayout(audio_hdr)

        a_form = QFormLayout()
        a_form.setSpacing(10)
        a_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        a_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(420)
        self.device_combo.addItem("Default System Microphone (Auto-Select Best)", None)
        devices = list_input_devices()
        curr_dev = self.config.get("device_index")
        dev_selected_idx = 0
        for i, dev in enumerate(devices, start=1):
            name = dev["name"]
            if len(name) > 48:
                name = name[:46] + "…"
            ch = dev.get("channels", dev.get("max_input_channels", 1))
            self.device_combo.addItem(f"{name} ({ch}ch)", dev["index"])
            if dev["index"] == curr_dev:
                dev_selected_idx = i
        self.device_combo.setCurrentIndex(dev_selected_idx)
        self.device_combo.currentIndexChanged.connect(self._restart_mic_monitor)
        a_form.addRow(self._make_label("Input Device:"), self.device_combo)

        # Live VU Audio Level Meter + dB Readout
        meter_widget = QWidget()
        meter_row = QHBoxLayout(meter_widget)
        meter_row.setContentsMargins(0, 0, 0, 0)
        meter_row.setSpacing(10)
        self.meter_bar = QProgressBar()
        self.meter_bar.setRange(0, 100)
        self.meter_bar.setValue(0)
        self.meter_bar.setTextVisible(False)
        meter_row.addWidget(self.meter_bar, stretch=1)

        self.db_label = QLabel("-60 dB")
        self.db_label.setFixedWidth(56)
        self.db_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.db_label.setStyleSheet("color: #94A3B8; font-size: 11.5px; font-family: 'Consolas', monospace;")
        meter_row.addWidget(self.db_label)
        a_form.addRow(self._make_label("Live Mic Level:"), meter_widget)

        audio_layout.addLayout(a_form)
        main_layout.addWidget(audio_card)

        # --- Card 3: Enhancements & Toggles ---
        toggles_card = QFrame()
        toggles_card.setProperty("class", "settingCard")
        toggles_layout = QVBoxLayout(toggles_card)
        toggles_layout.setContentsMargins(18, 15, 18, 15)
        toggles_layout.setSpacing(10)

        card3_title = QLabel("AI Post-Processing & Audio Feedback")
        card3_title.setProperty("class", "sectionHeader")
        toggles_layout.addWidget(card3_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.cleanup_check = ToggleSwitch("Remove fillers ('um', 'uh', 'like')")
        self.cleanup_check.setChecked(self.config.get("cleanup_filler", True))
        grid.addWidget(self.cleanup_check, 0, 0)

        self.commands_check = ToggleSwitch("Spoken commands ('new line', 'comma')")
        self.commands_check.setChecked(self.config.get("spoken_commands", True))
        grid.addWidget(self.commands_check, 0, 1)

        self.chimes_check = ToggleSwitch("Audio chimes (Start / Done)")
        self.chimes_check.setChecked(self.config.get("audio_feedback", True))
        grid.addWidget(self.chimes_check, 1, 0)

        self.vad_check = ToggleSwitch("Silero Voice Activity Detection")
        self.vad_check.setChecked(self.config.get("vad_filter", True))
        grid.addWidget(self.vad_check, 1, 1)

        toggles_layout.addLayout(grid)
        main_layout.addWidget(toggles_card)
        main_layout.addStretch()

        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        reset_btn = QPushButton("Reset Defaults")
        reset_btn.setObjectName("cancelBtn")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Preferences")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

    def _set_hotkey_preset(self, hk: str):
        self._stop_hotkey_recorder()
        self.hotkey_input.setText(hk)

    def _toggle_hotkey_recorder(self):
        if self._recording_hotkey:
            self._stop_hotkey_recorder()
        else:
            self._recording_hotkey = True
            self._captured_keys = []
            self.record_key_btn.setText("Press keys…")
            self.record_key_btn.setProperty("recording", "true")
            self.record_key_btn.style().unpolish(self.record_key_btn)
            self.record_key_btn.style().polish(self.record_key_btn)
            self.setFocus()

    def _stop_hotkey_recorder(self):
        if not self._recording_hotkey:
            return
        self._recording_hotkey = False
        self.record_key_btn.setText("Record Shortcut")
        self.record_key_btn.setProperty("recording", "false")
        self.record_key_btn.style().unpolish(self.record_key_btn)
        self.record_key_btn.style().polish(self.record_key_btn)

    def keyPressEvent(self, event: QKeyEvent):
        if self._recording_hotkey:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self._stop_hotkey_recorder()
                event.accept()
                return

            parts: List[str] = []
            mods = event.modifiers()
            if mods & Qt.KeyboardModifier.ControlModifier or key == Qt.Key.Key_Control:
                parts.append("ctrl")
            if mods & Qt.KeyboardModifier.MetaModifier or key in (Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R):
                parts.append("win")
            if mods & Qt.KeyboardModifier.AltModifier or key == Qt.Key.Key_Alt:
                parts.append("alt")
            if mods & Qt.KeyboardModifier.ShiftModifier or key == Qt.Key.Key_Shift:
                parts.append("shift")

            non_mod_map = {
                Qt.Key.Key_Space: "space",
                Qt.Key.Key_Tab: "tab",
                Qt.Key.Key_Return: "enter",
                Qt.Key.Key_Enter: "enter",
                Qt.Key.Key_CapsLock: "capslock",
                Qt.Key.Key_QuoteLeft: "`",
            }
            if key in non_mod_map:
                parts.append(non_mod_map[key])
            elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
                parts.append(f"f{key - Qt.Key.Key_F1 + 1}")
            elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                parts.append(chr(key).lower())
            elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
                parts.append(chr(key))

            if parts:
                unique_parts = list(dict.fromkeys(parts))
                self.hotkey_input.setText("+".join(unique_parts))
                if len(unique_parts) >= 2 or (len(unique_parts) == 1 and unique_parts[0].startswith("f")):
                    self._stop_hotkey_recorder()
            event.accept()
            return
        super().keyPressEvent(event)

    def _reset_defaults(self):
        self._stop_hotkey_recorder()
        self.mode_combo.setCurrentIndex(0)
        self.hotkey_input.setText("ctrl+win")
        self.model_combo.setCurrentIndex(0)
        self.style_combo.setCurrentIndex(0)
        self.device_combo.setCurrentIndex(0)
        self.cleanup_check.setChecked(True)
        self.commands_check.setChecked(True)
        self.chimes_check.setChecked(True)
        self.vad_check.setChecked(True)

    def showEvent(self, event):
        super().showEvent(event)
        self.config = load_config()
        self._start_mic_monitor()

    def closeEvent(self, event):
        self._stop_hotkey_recorder()
        self._stop_mic_monitor()
        super().closeEvent(event)

    def hideEvent(self, event):
        self._stop_hotkey_recorder()
        self._stop_mic_monitor()
        super().hideEvent(event)

    def _start_mic_monitor(self):
        self._stop_mic_monitor()
        dev_idx = self.device_combo.currentData()
        try:
            self._mic_monitor = AudioRecorder(
                device_index=dev_idx,
                level_callback=self._on_mic_level,
            )
            started = self._mic_monitor.start()
            if hasattr(self, "mic_status_label"):
                if started:
                    self.mic_status_label.setText("● Mic Active")
                    self.mic_status_label.setStyleSheet("""
                        background-color: #112220;
                        color: #34D399;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 3px 9px;
                        border-radius: 6px;
                        border: 1px solid #1E3A34;
                    """)
                else:
                    self.mic_status_label.setText("○ Standby")
                    self.mic_status_label.setStyleSheet("""
                        background-color: #1E1B18;
                        color: #FBBF24;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 3px 9px;
                        border-radius: 6px;
                        border: 1px solid #3D3122;
                    """)
        except Exception as e:
            logger.warning(f"Could not start mic meter: {e}")

    def _stop_mic_monitor(self):
        if self._mic_monitor:
            try:
                self._mic_monitor.stop()
            except Exception:
                pass
            self._mic_monitor = None
        if hasattr(self, "meter_bar"):
            self.meter_bar.setValue(0)
        if hasattr(self, "db_label"):
            self.db_label.setText("-60 dB")

    def _restart_mic_monitor(self):
        if self.isVisible():
            self._start_mic_monitor()

    def _on_mic_level(self, level: float):
        self.sig_mic_level.emit(float(level))

    def _update_meter_bar(self, level: float):
        val = int(min(100, (max(0.0, level) ** 0.5) * 220))
        if hasattr(self, "meter_bar"):
            self.meter_bar.setValue(val)
        if hasattr(self, "db_label"):
            if level <= 1e-5:
                db = -60
            else:
                db = max(-60, min(0, int(20.0 * math.log10(level))))
            self.db_label.setText(f"{db} dB")

    def done(self, r):
        self._stop_hotkey_recorder()
        self._stop_mic_monitor()
        super().done(r)

    def _save_settings(self):
        self._stop_hotkey_recorder()
        new_hotkey = self.hotkey_input.text().strip().lower() or "ctrl+win"
        new_model = self.model_combo.currentData()
        new_style = self.style_combo.currentData()
        new_device = self.device_combo.currentData()
        mode_val = self.mode_combo.currentData()

        if mode_val == "hi_to_en":
            new_lang = "hi"
            new_task = "translate"
        elif mode_val == "en_direct":
            new_lang = "en"
            new_task = "transcribe"
        elif mode_val == "auto_to_en":
            new_lang = "auto"
            new_task = "translate"
        elif mode_val == "hi_direct":
            new_lang = "hi"
            new_task = "transcribe"
        else:
            new_lang = "hi"
            new_task = "translate"

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
