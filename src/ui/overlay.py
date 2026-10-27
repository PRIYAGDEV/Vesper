# -*- coding: utf-8 -*-
"""
Vesper - Floating Audio-Reactive Status Pill Overlay
Crafted with UI/UX Pro Max design intelligence:
- Multi-layered frosted obsidian glassmorphism with ambient glow & specular rim lighting
- Per-bar independent spring-physics audio reactive waveform (11 harmonic bars)
- Live recording elapsed timer (0:00) and mode badge indicator
- Dynamic state transitions: Recording pulse, Transcribing aurora sweep, Done checkmark
- Non-focus-stealing, frameless, translucent, draggable anywhere on screen (right-click to reset position)
"""

import math
import time
from typing import List

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


class FloatingOverlay(QWidget):
    """Ultra-modern floating status pill with fluid multi-bar physics waveform and live timer."""

    sig_level_update = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Window flags: frameless, floating always on top, translucent, no taskbar entry
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.state = "idle"  # "idle", "recording", "transcribing", "done", "cancelled"
        self.status_text = ""
        self.mode_badge = "EN"

        # Spring-physics waveform state (11 independent harmonic bars)
        self._num_bars = 11
        self._phase = 0.0
        self._target_volume = 0.0
        self._volume = 0.0
        self._velocity = 0.0
        self._bar_heights: List[float] = [4.0] * self._num_bars
        self._bar_velocities: List[float] = [0.0] * self._num_bars
        self._beacon_pulse = 0.0
        self._record_start_ts = 0.0

        # Dragging state
        self._drag_position = QPoint()
        self._is_dragging = False
        self._custom_pos: bool = False

        # Thread-safe signal for audio callbacks coming from PortAudio worker thread
        self.sig_level_update.connect(self._apply_audio_level)

        # 60 FPS animation loop
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_tick)

        # Auto-hide timer for completion state
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_overlay)

        # Safety watchdog: prevents pill from ever getting stuck on screen
        self._watchdog_timer = QTimer(self)
        self._watchdog_timer.setSingleShot(True)
        self._watchdog_timer.timeout.connect(self.hide_overlay)

        self.setFixedSize(218, 50)

    def set_mode_badge(self, language: str = "en", task: str = "transcribe"):
        """Update the compact mode badge displayed on the pill."""
        if task == "translate" and language == "hi":
            self.mode_badge = "HI→EN"
        elif task == "translate":
            self.mode_badge = "AUTO→EN"
        elif language == "hi":
            self.mode_badge = "HI"
        else:
            self.mode_badge = "EN"
        if self.isVisible():
            self.update()

    def _reposition(self):
        if self._custom_pos:
            return
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.x() + (geom.width() - self.width()) // 2
            y = geom.y() + geom.height() - self.height() - 36
            self.move(x, y)

    def set_audio_level(self, level: float):
        """Update live audio level from microphone (0.0 to 1.0) safely from any thread."""
        scaled = min(1.0, math.sqrt(max(0.0, float(level))) * 3.5)
        self._target_volume = scaled

    def _apply_audio_level(self, scaled: float):
        self._target_volume = scaled

    def _on_tick(self):
        self._phase = (self._phase + 0.16) % (2.0 * math.pi)
        self._beacon_pulse = (self._beacon_pulse + 0.11) % (2.0 * math.pi)

        # Global volume spring
        stiffness = 0.40
        damping = 0.66
        force = (self._target_volume - self._volume) * stiffness
        self._velocity = (self._velocity + force) * damping
        self._volume = max(0.0, min(1.0, self._volume + self._velocity))

        # Per-bar harmonic spring simulation
        for i in range(self._num_bars):
            envelope = math.sin((i + 1) / (self._num_bars + 1) * math.pi)
            if self.state == "recording":
                harmonic = (
                    0.45 * math.sin(self._phase * 1.3 + i * 0.65)
                    + 0.35 * math.cos(self._phase * 2.1 - i * 0.9)
                    + 0.20 * math.sin(self._phase * 3.4 + i * 1.4)
                )
                norm_wave = 0.35 + 0.65 * max(0.0, (harmonic + 1.0) * 0.5)
                target_h = 4.0 + (7.5 * norm_wave + self._volume * 22.0 * (0.6 + 0.4 * norm_wave)) * envelope
            elif self.state == "transcribing":
                shimmer = 0.5 + 0.5 * math.sin(self._phase * 2.0 - i * 0.55)
                target_h = 4.0 + 16.0 * envelope * shimmer
            else:
                target_h = 4.0

            bar_force = (target_h - self._bar_heights[i]) * 0.45
            self._bar_velocities[i] = (self._bar_velocities[i] + bar_force) * 0.62
            self._bar_heights[i] = max(3.5, min(28.0, self._bar_heights[i] + self._bar_velocities[i]))

        self.update()

    def show_recording(self):
        self._hide_timer.stop()
        self._watchdog_timer.start(60000)  # 60s safety limit
        self.state = "recording"
        self.status_text = ""
        self._target_volume = 0.0
        self._volume = 0.0
        self._velocity = 0.0
        self._record_start_ts = time.monotonic()
        self.setFixedSize(218, 50)
        self._reposition()
        self.show()
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)  # ~60 FPS smooth rendering
        self.update()

    def show_transcribing(self):
        self._hide_timer.stop()
        self._watchdog_timer.start(30000)  # 30s safety limit
        self.state = "transcribing"
        self.status_text = "Transcribing"
        self.setFixedSize(208, 50)
        self._reposition()
        self.show()
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)
        self.update()

    def show_done(self, preview_text: str = ""):
        self.state = "done"
        self._anim_timer.stop()
        self._watchdog_timer.stop()
        if preview_text:
            cleaned = preview_text.replace("\n", " ").strip()
            if len(cleaned) > 36:
                cleaned = cleaned[:34] + "…"
            self.status_text = cleaned
            font = QFont("Segoe UI Variable Display", 10, QFont.Weight.DemiBold)
            fm = QFontMetrics(font)
            text_w = fm.horizontalAdvance(self.status_text)
            w = max(196, min(390, text_w + 68))
            self.setFixedSize(w, 50)
        else:
            self.status_text = "Pasted"
            self.setFixedSize(148, 50)
        self._reposition()
        self.update()
        self._hide_timer.start(1250)

    def show_cancelled(self):
        self.state = "cancelled"
        self._anim_timer.stop()
        self._watchdog_timer.stop()
        self.status_text = "No speech detected"
        self.setFixedSize(184, 50)
        self._reposition()
        self.update()
        self._hide_timer.start(950)

    def hide_overlay(self):
        self._anim_timer.stop()
        self._hide_timer.stop()
        self._watchdog_timer.stop()
        self.state = "idle"
        self.hide()

    # --- Mouse Drag Support to Reposition Anywhere (Right-click resets to bottom center) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._custom_pos = False
            self._reposition()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            self._custom_pos = True
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False

    def _format_elapsed(self) -> str:
        elapsed = max(0, int(time.monotonic() - self._record_start_ts))
        mins = elapsed // 60
        secs = elapsed % 60
        return f"{mins}:{secs:02d}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = float(self.width())
        h = float(self.height())

        # Outer ambient glow halo inside padded bounds
        capsule_rect = QRectF(3.0, 3.0, w - 6.0, h - 6.0)
        radius = capsule_rect.height() / 2.0

        # 1. Soft outer ambient glow
        glow_rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        glow_path = QPainterPath()
        glow_path.addRoundedRect(glow_rect, glow_rect.height() / 2.0, glow_rect.height() / 2.0)
        if self.state == "recording":
            glow_color = QColor(239, 68, 68, int(22 + 32 * self._volume))
        elif self.state == "transcribing":
            glow_color = QColor(139, 92, 246, 36)
        elif self.state == "done":
            glow_color = QColor(16, 185, 129, 34)
        else:
            glow_color = QColor(0, 0, 0, 40)
        painter.fillPath(glow_path, glow_color)

        # 2. Main Obsidian Frosted Glass Capsule
        path = QPainterPath()
        path.addRoundedRect(capsule_rect, radius, radius)

        bg_grad = QLinearGradient(0, capsule_rect.top(), 0, capsule_rect.bottom())
        bg_grad.setColorAt(0.0, QColor(18, 21, 32, 246))
        bg_grad.setColorAt(0.55, QColor(11, 13, 20, 248))
        bg_grad.setColorAt(1.0, QColor(8, 9, 15, 250))
        painter.fillPath(path, QBrush(bg_grad))

        # Subtle inner top highlight sheen
        sheen_rect = QRectF(capsule_rect.left() + 10, capsule_rect.top() + 1.0, capsule_rect.width() - 20, capsule_rect.height() * 0.42)
        sheen_grad = QLinearGradient(0, sheen_rect.top(), 0, sheen_rect.bottom())
        sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 22))
        sheen_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.save()
        painter.setClipPath(path)
        painter.fillRect(sheen_rect, QBrush(sheen_grad))
        painter.restore()

        # 3. Specular Rim Gradient Border
        rim_grad = QLinearGradient(0, capsule_rect.top(), w, capsule_rect.bottom())
        if self.state == "recording":
            rim_grad.setColorAt(0.0, QColor(248, 113, 113, int(130 + 90 * self._volume)))
            rim_grad.setColorAt(0.45, QColor(255, 255, 255, 45))
            rim_grad.setColorAt(1.0, QColor(139, 92, 246, 110))
            border_pen = QPen(QBrush(rim_grad), 1.35)
        elif self.state == "transcribing":
            sweep = 0.5 + 0.5 * math.sin(self._phase * 1.5)
            rim_grad.setColorAt(0.0, QColor(192, 132, 252, int(180 + 60 * sweep)))
            rim_grad.setColorAt(0.5, QColor(124, 58, 237, 175))
            rim_grad.setColorAt(1.0, QColor(236, 72, 153, int(160 + 70 * (1.0 - sweep))))
            border_pen = QPen(QBrush(rim_grad), 1.45)
        elif self.state == "done":
            rim_grad.setColorAt(0.0, QColor(52, 211, 153, 230))
            rim_grad.setColorAt(0.6, QColor(16, 185, 129, 140))
            rim_grad.setColorAt(1.0, QColor(5, 150, 105, 90))
            border_pen = QPen(QBrush(rim_grad), 1.4)
        elif self.state == "cancelled":
            rim_grad.setColorAt(0.0, QColor(248, 113, 113, 200))
            rim_grad.setColorAt(1.0, QColor(185, 28, 28, 80))
            border_pen = QPen(QBrush(rim_grad), 1.25)
        else:
            rim_grad.setColorAt(0.0, QColor(255, 255, 255, 45))
            rim_grad.setColorAt(1.0, QColor(255, 255, 255, 15))
            border_pen = QPen(QBrush(rim_grad), 1.1)

        painter.strokePath(path, border_pen)

        center_y = h / 2.0

        # --- Done State: Emerald Badge + Vector Checkmark + Preview ---
        if self.state == "done":
            badge_cx = 25.0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(16, 185, 129, 38))
            painter.drawEllipse(QPointF(badge_cx, center_y), 11.0, 11.0)
            painter.setBrush(QColor(16, 185, 129, 240))
            painter.drawEllipse(QPointF(badge_cx, center_y), 8.0, 8.0)

            check_pen = QPen(
                QColor(255, 255, 255),
                2.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(check_pen)
            painter.drawLine(QPointF(badge_cx - 3.5, center_y + 0.2), QPointF(badge_cx - 1.0, center_y + 2.8))
            painter.drawLine(QPointF(badge_cx - 1.0, center_y + 2.8), QPointF(badge_cx + 4.0, center_y - 2.6))

            font = QFont("Segoe UI Variable Display", 10, QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.setPen(QColor(241, 245, 249))
            text_rect = QRectF(44.0, 0, w - 56.0, h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.status_text)
            return

        # --- Cancelled State ---
        if self.state == "cancelled":
            font = QFont("Segoe UI Variable Display", 9, QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.setPen(QColor(252, 165, 165))
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.status_text)
            return

        # --- Recording State: Pulsing Ruby Beacon + 11-Bar Liquid Waveform + Live Timer ---
        if self.state == "recording":
            beacon_x = 22.0
            halo_radius = 6.5 + 2.5 * math.sin(self._beacon_pulse)
            halo_alpha = int(50 + 40 * math.sin(self._beacon_pulse))
            painter.setBrush(QColor(239, 68, 68, halo_alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(beacon_x, center_y), halo_radius, halo_radius)

            painter.setBrush(QColor(248, 113, 113, 255))
            painter.drawEllipse(QPointF(beacon_x, center_y), 4.0, 4.0)

            # 11-Bar Waveform centered in the middle section
            bar_w = 3.0
            spacing = 3.8
            total_w = self._num_bars * bar_w + (self._num_bars - 1) * spacing
            start_x = 40.0 + (w - 40.0 - 54.0 - total_w) / 2.0

            for i in range(self._num_bars):
                bx = start_x + i * (bar_w + spacing)
                bar_h = self._bar_heights[i]
                by = center_y - bar_h / 2.0

                bar_grad = QLinearGradient(0, by, 0, by + bar_h)
                intensity = min(1.0, (bar_h - 3.5) / 20.0)
                top_col = QColor(
                    int(248 - 55 * intensity),
                    int(250 - 95 * intensity),
                    255,
                    int(205 + 50 * intensity),
                )
                bot_col = QColor(
                    int(167 + 70 * intensity),
                    int(139 - 40 * intensity),
                    250,
                    int(180 + 70 * intensity),
                )
                bar_grad.setColorAt(0.0, top_col)
                bar_grad.setColorAt(1.0, bot_col)

                painter.setBrush(QBrush(bar_grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 1.5, 1.5)

            # Elapsed recording timer on the right
            timer_font = QFont("Segoe UI Variable Text", 9, QFont.Weight.DemiBold)
            painter.setFont(timer_font)
            painter.setPen(QColor(148, 163, 184))
            timer_rect = QRectF(w - 52.0, 0, 40.0, h)
            painter.drawText(
                timer_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                self._format_elapsed(),
            )
            return

        # --- Transcribing State: Aurora Waveform + "Transcribing" Label ---
        if self.state == "transcribing":
            bar_w = 2.8
            spacing = 3.2
            num_trans_bars = 7
            total_w = num_trans_bars * bar_w + (num_trans_bars - 1) * spacing
            start_x = 20.0

            for i in range(num_trans_bars):
                bx = start_x + i * (bar_w + spacing)
                envelope = math.sin((i + 1) / (num_trans_bars + 1) * math.pi)
                wave_factor = 0.5 + 0.5 * math.sin(self._phase * 2.2 - i * 0.7)
                bar_h = 4.0 + 14.0 * envelope * wave_factor
                by = center_y - bar_h / 2.0

                r = int(139 + 95 * wave_factor)
                g = int(92 + 40 * envelope)
                b = int(246)
                painter.setBrush(QColor(r, g, b, int(195 + 60 * wave_factor)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 1.4, 1.4)

            text_x = start_x + total_w + 12.0
            font = QFont("Segoe UI Variable Display", 9, QFont.Weight.DemiBold)
            painter.setFont(font)
            dots = "." * (int(self._phase / (math.pi / 2.0)) % 4)
            painter.setPen(QColor(226, 232, 240))
            painter.drawText(
                QRectF(text_x, 0, w - text_x - 14.0, h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                f"Transcribing{dots}",
            )
