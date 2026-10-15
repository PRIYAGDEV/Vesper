import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import pyperclip

logger = logging.getLogger("WisprClone.History")

import sys

def get_history_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "history.json"
    if Path("history.json").exists():
        return Path("history.json")
    return Path(__file__).resolve().parent.parent.parent / "history.json"

HISTORY_FILE = get_history_path()

HISTORY_STYLESHEET = """
QDialog {
    background-color: #181920;
    color: #F3F4F6;
    font-family: 'Segoe UI', sans-serif;
}
QLabel {
    color: #E5E7EB;
}
QScrollArea {
    border: 1px solid #2D3142;
    border-radius: 8px;
    background-color: #121318;
}
QScrollBar:vertical {
    border: none;
    background: #181920;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3F4458;
    border-radius: 4px;
}
QPushButton {
    background-color: #4F46E5;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #4338CA;
}
QPushButton#clearBtn {
    background-color: #EF4444;
}
QPushButton#clearBtn:hover {
    background-color: #DC2626;
}
QPushButton#copyBtn {
    background-color: #2D3142;
    color: #E5E7EB;
    border: 1px solid #3F4458;
}
QPushButton#copyBtn:hover {
    background-color: #4338CA;
    color: #FFFFFF;
}
"""


def load_history() -> List[dict]:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading history: {e}")
    return []


def save_history(history: List[dict]) -> None:
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving history: {e}")


def add_history_entry(text: str, limit: int = 20) -> None:
    if not text:
        return
    history = load_history()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": text
    }
    history.insert(0, entry)
    history = history[:limit]
    save_history(history)


class HistoryCard(QWidget):
    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.entry = entry

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        time_label = QLabel(entry.get("timestamp", ""))
        time_label.setFont(QFont("Segoe UI", 9))
        time_label.setStyleSheet("color: #9CA3AF;")
        info_layout.addWidget(time_label)

        text_label = QLabel(entry.get("text", ""))
        text_label.setFont(QFont("Segoe UI", 11))
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #F3F4F6;")
        info_layout.addWidget(text_label)

        layout.addLayout(info_layout, stretch=1)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setFixedWidth(64)
        self.copy_btn.clicked.connect(self._copy_text)
        layout.addWidget(self.copy_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.setStyleSheet("""
            QWidget {
                background-color: #1F222E;
                border-radius: 8px;
            }
        """)

    def _copy_text(self):
        pyperclip.copy(self.entry.get("text", ""))
        self.copy_btn.setText("Copied!")
        self.copy_btn.setStyleSheet("background-color: #10B981; color: white;")


class HistoryDialog(QDialog):
    """Dialog displaying the last 20 transcriptions with copy buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FreeFlow - Transcription History")
        self.setFixedSize(540, 500)
        self.setStyleSheet(HISTORY_STYLESHEET)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title = QLabel("Transcription History (Last 20)")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(title)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._clear_history)
        header_layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(header_layout)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_layout.setSpacing(8)

        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        self.refresh()

    def refresh(self):
        # Clear existing
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        history = load_history()
        if not history:
            empty_label = QLabel("No transcription history yet.\nHold hotkey to dictate anywhere.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #6B7280; font-size: 13px; padding: 40px;")
            self.cards_layout.addWidget(empty_label)
        else:
            for entry in history:
                card = HistoryCard(entry)
                self.cards_layout.addWidget(card)
        self.cards_layout.addStretch()

    def _clear_history(self):
        save_history([])
        self.refresh()
