import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

logger = logging.getLogger("WisprClone.Tray")


def create_tray_icon(is_recording: bool = False) -> QIcon:
    """Generate a crisp 64x64 high-DPI system tray pixmap icon with gradient depth."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    rect = QRectF(4, 4, 56, 56)
    path = QPainterPath()
    path.addRoundedRect(rect, 18, 18)

    if is_recording:
        grad = QLinearGradient(0, 4, 60, 60)
        grad.setColorAt(0.0, QColor(248, 113, 113))
        grad.setColorAt(1.0, QColor(220, 38, 38))
        painter.fillPath(path, QBrush(grad))
        painter.setPen(QPen(QColor(255, 255, 255, 90), 2.0))
        painter.drawPath(path)

        # Active recording acoustic waves
        bars = [16, 28, 36, 26, 18]
    else:
        grad = QLinearGradient(0, 4, 60, 60)
        grad.setColorAt(0.0, QColor(139, 92, 246))
        grad.setColorAt(1.0, QColor(79, 70, 229))
        painter.fillPath(path, QBrush(grad))
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1.8))
        painter.drawPath(path)

        # Signature Vesper harmonic waveform emblem
        bars = [12, 24, 34, 22, 14]

    bar_w = 4.4
    spacing = 4.2
    total_w = len(bars) * bar_w + (len(bars) - 1) * spacing
    start_x = (64.0 - total_w) / 2.0

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255, 245))
    for i, bh in enumerate(bars):
        bx = start_x + i * (bar_w + spacing)
        by = (64.0 - bh) / 2.0
        painter.drawRoundedRect(QRectF(bx, by, bar_w, bh), 2.2, 2.2)

    painter.end()
    return QIcon(pixmap)


class WisprTrayIcon(QSystemTrayIcon):
    """System tray icon with obsidian context menu, status header, and quick actions."""

    def __init__(
        self,
        hotkey_str: str = "ctrl+win",
        on_toggle_recording: Optional[Callable[[], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_open_history: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.hotkey_str = hotkey_str
        self.on_toggle_recording = on_toggle_recording
        self.on_open_settings = on_open_settings
        self.on_open_history = on_open_history
        self.on_quit = on_quit

        self.setIcon(create_tray_icon(is_recording=False))
        self.setToolTip(f"Vesper — Hold [{self.hotkey_str.upper()}] to dictate")

        self._init_menu()
        self.activated.connect(self._on_activated)

    def _init_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #111420;
                color: #F1F5F9;
                border: 1px solid #262E48;
                border-radius: 10px;
                padding: 6px;
                font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
                font-size: 12.5px;
            }
            QMenu::item {
                padding: 7px 22px;
                border-radius: 6px;
                margin: 1px 2px;
            }
            QMenu::item:disabled {
                color: #94A3B8;
                font-weight: 600;
            }
            QMenu::item:selected {
                background-color: #7C3AED;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1E2438;
                margin: 5px 8px;
            }
        """)

        title_act = QAction("🌙  Vesper — Local AI Dictation", menu)
        title_act.setEnabled(False)
        menu.addAction(title_act)

        self.hotkey_act = QAction(f"⌨  Shortcut: {self.hotkey_str.upper()}", menu)
        self.hotkey_act.setEnabled(False)
        menu.addAction(self.hotkey_act)

        menu.addSeparator()

        self.dictate_act = QAction("🎙  Start Recording", menu)
        if self.on_toggle_recording:
            self.dictate_act.triggered.connect(self.on_toggle_recording)
        menu.addAction(self.dictate_act)

        history_act = QAction("📜  Transcription History...", menu)
        if self.on_open_history:
            history_act.triggered.connect(self.on_open_history)
        menu.addAction(history_act)

        settings_act = QAction("⚙  Preferences...", menu)
        if self.on_open_settings:
            settings_act.triggered.connect(self.on_open_settings)
        menu.addAction(settings_act)

        menu.addSeparator()

        quit_act = QAction("✕  Quit Vesper", menu)
        if self.on_quit:
            quit_act.triggered.connect(self.on_quit)
        menu.addAction(quit_act)

        self.setContextMenu(menu)
        self._menu = menu

    def update_hotkey(self, new_hotkey: str):
        self.hotkey_str = new_hotkey
        self.hotkey_act.setText(f"⌨  Shortcut: {new_hotkey.upper()}")
        self.setToolTip(f"Vesper — Hold [{new_hotkey.upper()}] to dictate")

    def set_recording_state(self, is_recording: bool):
        self.setIcon(create_tray_icon(is_recording=is_recording))
        if is_recording:
            self.dictate_act.setText("⏹  Stop Recording")
        else:
            self.dictate_act.setText("🎙  Start Recording")

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.on_open_history:
                self.on_open_history()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.on_open_settings:
                self.on_open_settings()
