# -*- coding: utf-8 -*-
"""
Vesper - Transcription History Dialog
Crafted with UI/UX Pro Max design intelligence:
- Productivity metrics banner (Total Dictations, Words Dictated, Time Saved)
- Real-time instant search & filtering bar
- Deep obsidian cards (#121521) with word count badge, Copy & Delete actions
- Instant copy feedback with emerald checkmark badge
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

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
    background-color: #090B11;
    color: #F8FAFC;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
}
QLabel {
    color: #94A3B8;
}
QLineEdit {
    background-color: #121521;
    color: #F8FAFC;
    border: 1px solid #1E2438;
    border-radius: 9px;
    padding: 9px 14px;
    font-size: 13px;
}
QLineEdit:hover {
    border: 1px solid #2D3654;
}
QLineEdit:focus {
    border: 1px solid #7C3AED;
    background-color: #151929;
}
QScrollArea {
    border: 1px solid #1E2438;
    border-radius: 12px;
    background-color: #0C0E17;
}
QScrollBar:vertical {
    border: none;
    background: #0C0E17;
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
    background: #3B4463;
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
    background-color: #1D1522;
    color: #F87171;
    border: 1px solid #3A202B;
}
QPushButton#clearBtn:hover {
    background-color: #7F1D1D;
    color: #FFFFFF;
    border: 1px solid #EF4444;
}
QPushButton#copyBtn {
    background-color: #1A1F33;
    color: #E2E8F0;
    border: 1px solid #2B334E;
    font-size: 12px;
    font-weight: 600;
    border-radius: 6px;
    padding: 5px 12px;
}
QPushButton#copyBtn:hover {
    background-color: #7C3AED;
    color: #FFFFFF;
    border: 1px solid #8B5CF6;
}
QPushButton#deleteCardBtn {
    background-color: transparent;
    color: #64748B;
    border: 1px solid transparent;
    font-size: 12px;
    font-weight: 600;
    border-radius: 6px;
    padding: 4px 8px;
}
QPushButton#deleteCardBtn:hover {
    background-color: #2A1621;
    color: #F87171;
    border: 1px solid #4C1D2E;
}
QFrame.statCard {
    background-color: #121521;
    border: 1px solid #1E2438;
    border-radius: 10px;
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


class StatBadgeCard(QFrame):
    """Compact metric card for the top statistics bar."""

    def __init__(self, label: str, value: str, accent_color: str = "#A78BFA", parent=None):
        super().__init__(parent)
        self.setProperty("class", "statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(2)

        self.val_label = QLabel(value)
        self.val_label.setFont(QFont("Segoe UI Variable Display", 14, QFont.Weight.Bold))
        self.val_label.setStyleSheet(f"color: {accent_color}; background: transparent; border: none;")
        layout.addWidget(self.val_label)

        self.title_label = QLabel(label)
        self.title_label.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.Medium))
        self.title_label.setStyleSheet("color: #64748B; background: transparent; border: none;")
        layout.addWidget(self.title_label)

    def set_value(self, value: str):
        self.val_label.setText(value)


class HistoryCard(QFrame):
    """Sleek obsidian transcription card with word count, copy feedback, and delete action."""

    def __init__(
        self,
        entry: dict,
        on_delete: Optional[Callable[[dict], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.entry = entry
        self.on_delete = on_delete

        self.setStyleSheet("""
            QFrame {
                background-color: #121521;
                border: 1px solid #1E2438;
                border-radius: 10px;
            }
            QFrame:hover {
                border: 1px solid #313B5C;
                background-color: #161A29;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Header: Timestamp + Word count pill
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        time_label = QLabel(entry.get("timestamp", ""))
        time_label.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.DemiBold))
        time_label.setStyleSheet("color: #64748B; background: transparent; border: none;")
        meta_row.addWidget(time_label)

        text_content = entry.get("text", "")
        word_count = len(text_content.split())
        wc_label = QLabel(f"• {word_count} {'word' if word_count == 1 else 'words'}")
        wc_label.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.Medium))
        wc_label.setStyleSheet("color: #475569; background: transparent; border: none;")
        meta_row.addWidget(wc_label)
        meta_row.addStretch()
        info_layout.addLayout(meta_row)

        # Body: Transcribed text
        text_label = QLabel(text_content)
        text_label.setFont(QFont("Segoe UI Variable Text", 10.5))
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_label.setStyleSheet("color: #F1F5F9; background: transparent; border: none; line-height: 1.45;")
        info_layout.addWidget(text_label)

        layout.addLayout(info_layout, stretch=1)

        # Action Buttons Column
        actions_col = QHBoxLayout()
        actions_col.setSpacing(6)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setFixedWidth(68)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_text)
        actions_col.addWidget(self.copy_btn, alignment=Qt.AlignmentFlag.AlignTop)

        if self.on_delete:
            del_btn = QPushButton("✕")
            del_btn.setObjectName("deleteCardBtn")
            del_btn.setFixedWidth(28)
            del_btn.setToolTip("Delete this entry")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda: self.on_delete(self.entry))
            actions_col.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addLayout(actions_col)

    def _copy_text(self):
        try:
            pyperclip.copy(self.entry.get("text", ""))
        except Exception as e:
            logger.debug(f"Copy to clipboard failed: {e}")
        self.copy_btn.setText("✓ Copied")
        self.copy_btn.setStyleSheet("background-color: #10B981; color: white; border: 1px solid #10B981;")
        QTimer.singleShot(1400, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.copy_btn.setText("Copy")
        self.copy_btn.setStyleSheet("")


class HistoryDialog(QDialog):
    """Full-featured transcription history with stats dashboard, instant search, and item actions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vesper — Transcription History")
        self.setFixedSize(620, 620)
        self.setStyleSheet(HISTORY_STYLESHEET)
        self._all_history: List[dict] = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(13)

        # Top Bar: Title + Counter + Clear Button
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("Transcription History")
        title.setFont(QFont("Segoe UI Variable Display", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #F8FAFC;")
        title_col.addWidget(title)

        sub = QLabel("Click any card to select text or copy back to your clipboard")
        sub.setStyleSheet("color: #64748B; font-size: 11.5px;")
        title_col.addWidget(sub)
        header.addLayout(title_col)

        self.count_badge = QLabel("0 items")
        self.count_badge.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.DemiBold))
        self.count_badge.setStyleSheet("""
            background-color: #171B2E;
            color: #A78BFA;
            padding: 4px 10px;
            border-radius: 7px;
            border: 1px solid #2A3252;
        """)
        header.addWidget(self.count_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("clearBtn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_history)
        header.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        main_layout.addLayout(header)

        # Productivity Metrics Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.stat_clips = StatBadgeCard("DICTATIONS", "0", "#A78BFA")
        self.stat_words = StatBadgeCard("WORDS SPOKEN", "0", "#38BDF8")
        self.stat_saved = StatBadgeCard("EST. TIME SAVED", "0s", "#34D399")
        stats_row.addWidget(self.stat_clips, stretch=1)
        stats_row.addWidget(self.stat_words, stretch=1)
        stats_row.addWidget(self.stat_saved, stretch=1)
        main_layout.addLayout(stats_row)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Filter transcriptions by keyword...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_history)
        main_layout.addWidget(self.search_input)

        # Scroll Area for Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #0C0E17;")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(12, 12, 12, 12)
        self.cards_layout.setSpacing(10)

        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll, stretch=1)

        self.refresh()

    def _update_stats(self):
        total_clips = len(self._all_history)
        total_words = sum(len(e.get("text", "").split()) for e in self._all_history)
        # Average typing speed ~40 WPM vs speaking ~150 WPM -> ~1.1 sec saved per word
        sec_saved = int(round(total_words * 1.1))
        if sec_saved < 60:
            saved_str = f"{sec_saved}s"
        else:
            saved_str = f"{sec_saved // 60}m {sec_saved % 60}s"

        self.stat_clips.set_value(str(total_clips))
        self.stat_words.set_value(f"{total_words:,}")
        self.stat_saved.set_value(saved_str)
        self.count_badge.setText(f"{total_clips} {'item' if total_clips == 1 else 'items'}")

    def refresh(self):
        self._all_history = load_history()
        self._update_stats()
        self._filter_history(self.search_input.text())

    def _delete_entry(self, entry: dict):
        if entry in self._all_history:
            self._all_history.remove(entry)
            save_history(self._all_history)
            self.refresh()

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
                msg = f"No transcriptions match \"{query}\"."
            else:
                msg = "No transcription history yet.\nHold your Push-to-Talk shortcut anywhere to start dictating."
            empty_label = QLabel(msg)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; font-size: 13px; padding: 54px; line-height: 1.5;")
            self.cards_layout.addWidget(empty_label)
        else:
            for entry in filtered:
                card = HistoryCard(entry, on_delete=self._delete_entry)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _clear_history(self):
        save_history([])
        self.refresh()
