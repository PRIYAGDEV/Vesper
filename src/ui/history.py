# -*- coding: utf-8 -*-
"""
Vesper - Transcription History Dialog
Crafted with UI/UX Pro Max design intelligence:
- Real-time instant search & filtering bar
- Deep obsidian cards (#131622) with micro-elevation on hover
- Instant copy feedback with checkmark badge
- Item count indicator and clean empty state
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import pyperclip
from src.config import get_app_data_dir

logger = logging.getLogger("WisprClone.History")
_history_lock = threading.Lock()


def get_history_path() -> Path:
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve().parent / "history.json"
        if exe_path.exists() and os.access(exe_path.parent, os.W_OK):
            return exe_path
        return get_app_data_dir() / "history.json"
    if Path("history.json").exists() and os.access(Path("."), os.W_OK):
        return Path("history.json")
    return get_app_data_dir() / "history.json"


HISTORY_FILE = get_history_path()

HISTORY_STYLESHEET = """
QDialog {
    background-color: #0B0D14;
    color: #F8FAFC;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
}
QLabel {
    color: #94A3B8;
}
QLineEdit {
    background-color: #131622;
    color: #F8FAFC;
    border: 1px solid #1E2333;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #7C3AED;
    background-color: #161A28;
}
QScrollArea {
    border: 1px solid #1E2333;
    border-radius: 10px;
    background-color: #0E1019;
}
QScrollBar:vertical {
    border: none;
    background: #0E1019;
    width: 8px;
    border-radius: 4px;
    margin: 4px 2px 4px 0;
}
QScrollBar::handle:vertical {
    background: #252B3E;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #333C57;
}
QPushButton {
    background-color: #7C3AED;
    color: #FFFFFF;
    border: none;
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #6D28D9;
}
QPushButton#clearBtn {
    background-color: #1F1924;
    color: #F87171;
    border: 1px solid #37212B;
}
QPushButton#clearBtn:hover {
    background-color: #7F1D1D;
    color: #FFFFFF;
}
QPushButton#copyBtn {
    background-color: #1E2333;
    color: #E2E8F0;
    border: 1px solid #2B3349;
    font-size: 12px;
    font-weight: 500;
    border-radius: 6px;
    padding: 5px 12px;
}
QPushButton#copyBtn:hover {
    background-color: #7C3AED;
    color: #FFFFFF;
    border: 1px solid #7C3AED;
}
"""


def load_history() -> List[dict]:
    with _history_lock:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception as e:
                logger.error(f"Error loading history: {e}")
        return []


def save_history(history: List[dict]) -> None:
    with _history_lock:
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = HISTORY_FILE.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            tmp_path.replace(HISTORY_FILE)
        except Exception as e:
            logger.error(f"Error saving history: {e}")


def add_history_entry(text: str, limit: int = 20) -> None:
    if not text:
        return
    history = load_history()
    entry = {
        "timestamp": datetime.now().strftime("%b %d, %I:%M %p"),
        "text": text,
    }
    history.insert(0, entry)
    history = history[:limit]
    save_history(history)


class HistoryCard(QFrame):
    """Sleek obsidian transcription card with instant copy feedback."""

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.entry = entry

        self.setStyleSheet("""
            QFrame {
                background-color: #131622;
                border: 1px solid #1E2333;
                border-radius: 10px;
            }
            QFrame:hover {
                border: 1px solid #2B3349;
                background-color: #161928;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Header: Timestamp badge
        time_label = QLabel(entry.get("timestamp", ""))
        time_label.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.Medium))
        time_label.setStyleSheet("color: #64748B; background: transparent; border: none;")
        info_layout.addWidget(time_label)

        # Body: Transcribed text
        text_label = QLabel(entry.get("text", ""))
        text_label.setFont(QFont("Segoe UI Variable Text", 11))
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #F1F5F9; background: transparent; border: none; line-height: 1.4;")
        info_layout.addWidget(text_label)

        layout.addLayout(info_layout, stretch=1)

        # Copy Action Button
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setFixedWidth(68)
        self.copy_btn.clicked.connect(self._copy_text)
        layout.addWidget(self.copy_btn, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

    def _copy_text(self):
        try:
            pyperclip.copy(self.entry.get("text", ""))
        except Exception as e:
            logger.debug(f"Copy to clipboard failed: {e}")
        self.copy_btn.setText("Copied!")
        self.copy_btn.setStyleSheet("background-color: #10B981; color: white; border: 1px solid #10B981;")
        # Reset text back after 1.4 seconds
        QTimer.singleShot(1400, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.copy_btn.setText("Copy")
        self.copy_btn.setStyleSheet("")


class HistoryDialog(QDialog):
    """Full-featured transcription history with instant search and count badge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vesper - Transcription History")
        self.setFixedSize(580, 560)
        self.setStyleSheet(HISTORY_STYLESHEET)
        self._all_history: List[dict] = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 20, 22, 20)
        main_layout.setSpacing(12)

        # Top Bar: Title + Counter + Clear Button
        header = QHBoxLayout()
        title = QLabel("Transcription History")
        title.setFont(QFont("Segoe UI Variable Display", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        header.addWidget(title)

        self.count_badge = QLabel("0 items")
        self.count_badge.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.DemiBold))
        self.count_badge.setStyleSheet("""
            background-color: #1E2333;
            color: #94A3B8;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid #2E364F;
        """)
        header.addWidget(self.count_badge)
        header.addStretch()

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._clear_history)
        header.addWidget(clear_btn)
        main_layout.addLayout(header)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search past transcriptions...")
        self.search_input.textChanged.connect(self._filter_history)
        main_layout.addWidget(self.search_input)

        # Scroll Area for Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(12, 12, 12, 12)
        self.cards_layout.setSpacing(10)

        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        self.refresh()

    def refresh(self):
        self._all_history = load_history()
        self.count_badge.setText(f"{len(self._all_history)} items")
        self._filter_history(self.search_input.text())

    def _filter_history(self, query: str):
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query_clean = query.strip().lower()
        filtered = [
            e for e in self._all_history
            if not query_clean or query_clean in e.get("text", "").lower()
        ]

        if not filtered:
            if query_clean:
                msg = f"No transcriptions match '{query}'."
            else:
                msg = "No transcription history yet.\nHold hotkey to dictate anywhere."
            empty_label = QLabel(msg)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; font-size: 13px; padding: 48px;")
            self.cards_layout.addWidget(empty_label)
        else:
            for entry in filtered:
                card = HistoryCard(entry)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _clear_history(self):
        save_history([])
        self.refresh()
