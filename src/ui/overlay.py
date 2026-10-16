# -*- coding: utf-8 -*-
"""
FreeFlow - Floating Audio-Reactive Status Pill Overlay
Crafted with UI/UX Pro Max design intelligence:
- Ultra-premium frosted obsidian glassmorphism with specular rim lighting
- Liquid spring-physics audio reactive waveform (9 harmonic bars)
- Dynamic state transitions: Recording pulse, Transcribing aurora sweep, Done checkmark
- Non-focus-stealing, frameless, translucent, draggable anywhere on screen
"""

import math
from PySide6.QtCore import Qt, QPoint, QRectF, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QBrush,
)
from PySide6.QtWidgets import QWidget


class FloatingOverlay(QWidget):
    """Ultra-modern floating status pill with fluid physics waveform."""

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
        
        # Spring-physics waveform state
        self._phase = 0.0
        self._target_volume = 0.0
        self._volume = 0.0
        self._velocity = 0.0
        self._beacon_pulse = 0.0
        
        # Dragging state
        self._drag_position = QPoint()
        self._is_dragging = False
        self._custom_pos: bool = False

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

        self.setFixedSize(164, 46)

    def _reposition(self):
        if self._custom_pos:
            return
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = (geom.width() - self.width()) // 2
            y = geom.height() - self.height() - 80
            self.move(x, y)

    def set_audio_level(self, level: float):
        """Update live audio level from microphone (0.0 to 1.0)."""
        # Non-linear acoustic compression curve for sensitive voice visualization
        scaled = min(1.0, math.sqrt(max(0.0, level)) * 3.4)
        self._target_volume = scaled

    def _on_tick(self):
        self._phase = (self._phase + 0.18) % (2.0 * math.pi)
        self._beacon_pulse = (self._beacon_pulse + 0.12) % (2.0 * math.pi)

        # 2nd-order spring damping physics for organic liquid bounce
        stiffness = 0.38
        damping = 0.68
        force = (self._target_volume - self._volume) * stiffness
        self._velocity = (self._velocity + force) * damping
        self._volume = max(0.0, min(1.0, self._volume + self._velocity))

        self.update()

    def show_recording(self):
        self._hide_timer.stop()
        self._watchdog_timer.start(45000)  # 45s safety limit
        self.state = "recording"
        self.status_text = ""
        self._target_volume = 0.0
        self._volume = 0.0
        self._velocity = 0.0
        self.setFixedSize(164, 46)
        self._reposition()
        self.show()
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)  # ~60 FPS smooth rendering
        self.update()

    def show_transcribing(self):
        self._hide_timer.stop()
        self._watchdog_timer.start(12000)  # 12s safety limit
        self.state = "transcribing"
        self.status_text = ""
        self.setFixedSize(164, 46)
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
            if len(cleaned) > 32:
                cleaned = cleaned[:30] + "..."
            self.status_text = cleaned
            # Expand width smoothly according to preview length
            w = max(190, min(360, 60 + len(self.status_text) * 8))
            self.setFixedSize(w, 46)
        else:
            self.status_text = "Ready"
            self.setFixedSize(140, 46)
        self._reposition()
        self.update()
        self._hide_timer.start(1100)

    def show_cancelled(self):
        self.state = "cancelled"
        self._anim_timer.stop()
        self._watchdog_timer.stop()
        self.status_text = "Cancelled"
        self.setFixedSize(140, 46)
        self._reposition()
        self.update()
        self._hide_timer.start(800)

    def hide_overlay(self):
        self._anim_timer.stop()
        self._hide_timer.stop()
        self._watchdog_timer.stop()
        self.state = "idle"
        self.hide()

    # --- Mouse Drag Support to Reposition Anywhere ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            self._custom_pos = True
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        radius = h / 2.0

        # Outer capsule geometry
        capsule_rect = QRectF(1.5, 1.5, w - 3.0, h - 3.0)
        path = QPainterPath()
        path.addRoundedRect(capsule_rect, radius, radius)

        # 1. Multi-layered Obsidian Frosted Glass
        # Base glass fill
        painter.fillPath(path, QColor(11, 13, 19, 238))

        # 2. Specular rim gradient (light reflection from top)
        rim_grad = QLinearGradient(0, 0, 0, h)
        if self.state == "recording":
            rim_grad.setColorAt(0.0, QColor(255, 255, 255, int(70 + 80 * self._volume)))
            rim_grad.setColorAt(0.5, QColor(255, 255, 255, 20))
            rim_grad.setColorAt(1.0, QColor(239, 68, 68, 60))
            border_pen = QPen(QBrush(rim_grad), 1.2)
        elif self.state == "transcribing":
            rim_grad.setColorAt(0.0, QColor(192, 132, 252, 220))
            rim_grad.setColorAt(0.5, QColor(139, 92, 246, 160))
            rim_grad.setColorAt(1.0, QColor(236, 72, 153, 140))
            border_pen = QPen(QBrush(rim_grad), 1.3)
        elif self.state == "done":
            rim_grad.setColorAt(0.0, QColor(74, 222, 128, 220))
            rim_grad.setColorAt(1.0, QColor(34, 197, 94, 80))
            border_pen = QPen(QBrush(rim_grad), 1.3)
        elif self.state == "cancelled":
            rim_grad.setColorAt(0.0, QColor(248, 113, 113, 200))
            rim_grad.setColorAt(1.0, QColor(185, 28, 28, 80))
            border_pen = QPen(QBrush(rim_grad), 1.2)
        else:
            rim_grad.setColorAt(0.0, QColor(255, 255, 255, 40))
            rim_grad.setColorAt(1.0, QColor(255, 255, 255, 10))
            border_pen = QPen(QBrush(rim_grad), 1.0)

        painter.strokePath(path, border_pen)

        center_y = h / 2.0

        # --- Done State: Vector Checkmark + Clean Preview ---
        if self.state == "done":
            # Vector checkmark icon
            icon_x = 20.0
            icon_y = center_y
            check_pen = QPen(QColor(34, 197, 94), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(check_pen)
            painter.drawLine(QPoint(int(icon_x), int(icon_y)), QPoint(int(icon_x + 4), int(icon_y + 4)))
            painter.drawLine(QPoint(int(icon_x + 4), int(icon_y + 4)), QPoint(int(icon_x + 11), int(icon_y - 5)))

            # Preview text
            font = QFont("Segoe UI Variable Display", 10, QFont.Weight.Medium)
            painter.setFont(font)
            painter.setPen(QColor(241, 245, 249))
            text_rect = QRectF(icon_x + 18, 0, w - (icon_x + 28), h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.status_text)
            return

        # --- Cancelled State ---
        if self.state == "cancelled":
            font = QFont("Segoe UI Variable Display", 10, QFont.Weight.Medium)
            painter.setFont(font)
            painter.setPen(QColor(248, 113, 113))
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self.status_text)
            return

        # --- Recording Beacon (Pulsing Ruby Dot) ---
        beacon_x = 22.0
        if self.state == "recording":
            # Halo glow
            halo_radius = 5.0 + 2.5 * math.sin(self._beacon_pulse)
            halo_alpha = int(60 + 40 * math.sin(self._beacon_pulse))
            painter.setBrush(QColor(239, 68, 68, halo_alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(beacon_x), int(center_y)), int(halo_radius), int(halo_radius))

            # Core ruby dot
            painter.setBrush(QColor(239, 68, 68, 255))
            painter.drawEllipse(QPoint(int(beacon_x), int(center_y)), 3, 3)

        # --- Liquid Audio-Reactive Waveform (9 Harmonic Bars) ---
        num_bars = 9
        bar_w = 3.0
        spacing = 4.5
        total_w = num_bars * bar_w + (num_bars - 1) * spacing
        # If recording, offset slightly right to leave room for beacon
        start_x = (w - total_w) / 2.0 + (6.0 if self.state == "recording" else 0.0)

        for i in range(num_bars):
            bx = start_x + i * (bar_w + spacing)
            # Bell curve envelope for symmetric center emphasis
            envelope = math.sin((i + 1) / (num_bars + 1) * math.pi)

            if self.state == "recording":
                # Idle fluid breathing wave
                idle_wave = 0.4 + 0.6 * math.sin(self._phase + i * 0.75)
                # Live acoustic expansion
                mic_expand = self._volume * 22.0 * envelope
                bar_h = 3.5 + 8.0 * envelope * idle_wave + mic_expand
                
                # Dynamic gradient based on voice power
                alpha = int(160 + 95 * min(1.0, idle_wave * 0.3 + self._volume * 0.8))
                bar_color = QColor(255, 255, 255, min(255, alpha))
            else:
                # Transcribing aurora sweep
                wave_factor = 0.5 + 0.5 * math.sin(self._phase * 1.8 + i * 0.9)
                bar_h = 3.5 + 15.0 * envelope * wave_factor
                # Smooth purple to pink color shift
                r = int(139 + 70 * wave_factor)
                g = int(92 + 50 * envelope)
                b = int(246 + 9 * wave_factor)
                bar_color = QColor(r, g, b, int(180 + 75 * wave_factor))

            by = center_y - bar_h / 2.0
            painter.setBrush(bar_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 1.5, 1.5)
