import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

logger = logging.getLogger("WisprClone.Tray")


def create_tray_icon(is_recording: bool = False) -> QIcon:
    """Generate a crisp 64x64 system tray pixmap icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if is_recording:
        # Red pulsing circle for recording
        painter.setBrush(QColor(239, 68, 68))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(6, 6, 52, 52)

        # White recording dot/center
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(22, 22, 20, 20)
    else:
        # Indigo/Violet circle matching Wispr Flow brand
        painter.setBrush(QColor(99, 102, 241))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(6, 6, 52, 52)

        # White microphone shape
        painter.setBrush(QColor(255, 255, 255))
        # Mic body capsule
        painter.drawRoundedRect(25, 14, 14, 24, 7, 7)
        # Stand base
        painter.drawRect(30, 42, 4, 8)
        painter.drawRect(22, 48, 20, 4)

    painter.end()
    return QIcon(pixmap)


class WisprTrayIcon(QSystemTrayIcon):
    """System tray icon with right-click menu, status, and settings access."""

    def __init__(
        self,
        hotkey_str: str = "ctrl+win",
        on_toggle_recording: Optional[Callable[[], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_open_history: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.hotkey_str = hotkey_str
        self.on_toggle_recording = on_toggle_recording
        self.on_open_settings = on_open_settings
        self.on_open_history = on_open_history
        self.on_quit = on_quit

        self.setIcon(create_tray_icon(is_recording=False))
        self.setToolTip(f"Vesper - Hold [{self.hotkey_str.upper()}] to dictate")

        self._init_menu()
        self.activated.connect(self._on_activated)

    def _init_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1F222E;
                color: #F3F4F6;
                border: 1px solid #3F4458;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4F46E5;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #374151;
                margin: 4px 8px;
            }
        """)

        # Title action
        title_act = QAction("Vesper", menu)
        title_act.setEnabled(False)
        menu.addAction(title_act)

        self.hotkey_act = QAction(f"Hotkey: {self.hotkey_str.upper()}", menu)
        self.hotkey_act.setEnabled(False)
        menu.addAction(self.hotkey_act)

        menu.addSeparator()

        self.dictate_act = QAction("Toggle Recording", menu)
        if self.on_toggle_recording:
            self.dictate_act.triggered.connect(self.on_toggle_recording)
        menu.addAction(self.dictate_act)

        history_act = QAction("Transcription History...", menu)
        if self.on_open_history:
            history_act.triggered.connect(self.on_open_history)
        menu.addAction(history_act)

        settings_act = QAction("Settings...", menu)
        if self.on_open_settings:
            settings_act.triggered.connect(self.on_open_settings)
        menu.addAction(settings_act)

        menu.addSeparator()

        quit_act = QAction("Quit", menu)
        if self.on_quit:
            quit_act.triggered.connect(self.on_quit)
        menu.addAction(quit_act)

        self.setContextMenu(menu)

    def update_hotkey(self, new_hotkey: str):
        self.hotkey_str = new_hotkey
        self.hotkey_act.setText(f"Hotkey: {new_hotkey.upper()}")
        self.setToolTip(f"Wispr Flow Clone - Hold [{new_hotkey.upper()}] to dictate")

    def set_recording_state(self, is_recording: bool):
        self.setIcon(create_tray_icon(is_recording=is_recording))
        if is_recording:
            self.dictate_act.setText("Stop Recording")
        else:
            self.dictate_act.setText("Start Recording")

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click opens history or settings
            if self.on_open_history:
                self.on_open_history()
