import math
from PySide6.QtCore import Qt, QTimer, QRectF, QPoint
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QGuiApplication,
    QLinearGradient,
    QBrush,
)
from PySide6.QtWidgets import QWidget


class FloatingOverlay(QWidget):
    """Ultra-modern floating status capsule replicating Wispr Flow's signature design.

    Features:
    - Audio-reactive live microphone waveform (reacts to real voice amplitude).
    - Violet/purple gradient shimmer during transcription.
    - Clean text preview & green checkmark on completion.
    - Click & drag anywhere to reposition on screen.
    - Non-focus stealing, transparent, frameless.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.state = "idle"  # "idle", "recording", "transcribing", "done", "cancelled"
        self.status_text = ""
        self._bars_phase = 0.0
        self._target_volume = 0.0
        self._current_volume = 0.0
        self._drag_position = QPoint()
        self._is_dragging = False
        self._custom_pos: bool = False

        # 60 FPS animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_tick)

        # Auto-hide timer for completion state
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_overlay)

        # Safety watchdog timer: guarantees pill never gets stuck on screen
        self._watchdog_timer = QTimer(self)
        self._watchdog_timer.setSingleShot(True)
        self._watchdog_timer.timeout.connect(self.hide_overlay)

        self.setFixedSize(146, 44)

    def _reposition(self):
        if self._custom_pos:
            return
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = (geom.width() - self.width()) // 2
            y = geom.height() - self.height() - 75
            self.move(x, y)

    def set_audio_level(self, level: float):
        """Update live audio level from microphone (0.0 to 1.0)."""
        # Boost quiet voices for visible reactive bounce
        scaled = min(1.0, math.sqrt(max(0.0, level)) * 3.2)
        self._target_volume = scaled

    def _on_tick(self):
        self._bars_phase = (self._bars_phase + 0.25) % (2 * math.pi)
        # Smooth volume interpolation
        self._current_volume += (self._target_volume - self._current_volume) * 0.35
        self.update()

    def show_recording(self):
        self._hide_timer.stop()
        self._watchdog_timer.start(45000)  # 45s safety limit
        self.state = "recording"
        self.status_text = ""
        self._target_volume = 0.0
        self._current_volume = 0.0
        self.setFixedSize(146, 44)
        self._reposition()
        self.show()
        if not self._anim_timer.isActive():
            self._anim_timer.start(24)  # ~40 FPS smooth rendering
        self.update()

    def show_transcribing(self):
        self._hide_timer.stop()
        self._watchdog_timer.start(12000)  # 12s safety limit
        self.state = "transcribing"
        self.status_text = ""
        self.setFixedSize(146, 44)
        self._reposition()
        self.show()
        if not self._anim_timer.isActive():
            self._anim_timer.start(24)
        self.update()

    def show_done(self, preview_text: str = ""):
        self.state = "done"
        self._anim_timer.stop()
        self._watchdog_timer.stop()
        if preview_text:
            cleaned = preview_text.replace("\n", " ").strip()
            if len(cleaned) > 28:
                cleaned = cleaned[:26] + "..."
            self.status_text = f"\"{cleaned}\""
            # Expand width dynamically
            w = max(180, min(320, 40 + len(self.status_text) * 8))
            self.setFixedSize(w, 44)
        else:
            self.status_text = "Done"
            self.setFixedSize(130, 44)
        self._reposition()
        self.update()
        self._hide_timer.start(1000)

    def show_cancelled(self):
        self.state = "cancelled"
        self._anim_timer.stop()
        self._watchdog_timer.stop()
        self.status_text = "Cancelled"
        self.setFixedSize(130, 44)
        self._reposition()
        self.update()
        self._hide_timer.start(750)

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

        # Background capsule with double border
        w = float(self.width())
        h = float(self.height())
        radius = h / 2.0
        capsule_rect = QRectF(1.5, 1.5, w - 3.0, h - 3.0)
        path = QPainterPath()
        path.addRoundedRect(capsule_rect, radius, radius)

        # Glassmorphic deep obsidian dark background
        painter.fillPath(path, QColor(14, 15, 20, 245))

        # Dynamic glowing border
        if self.state == "recording":
            # White glow with audio intensity
            border_alpha = int(60 + 120 * self._current_volume)
            border_pen = QPen(QColor(255, 255, 255, border_alpha), 1.2)
        elif self.state == "transcribing":
            # Purple / violet gradient sweep border
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, QColor(139, 92, 246, 180))
            grad.setColorAt(0.5, QColor(192, 132, 252, 240))
            grad.setColorAt(1.0, QColor(236, 72, 153, 180))
            border_pen = QPen(QBrush(grad), 1.4)
        elif self.state == "done":
            # Vibrant emerald green border
            border_pen = QPen(QColor(34, 197, 94, 200), 1.3)
        elif self.state == "cancelled":
            # Soft red border
            border_pen = QPen(QColor(239, 68, 68, 180), 1.3)
        else:
            border_pen = QPen(QColor(255, 255, 255, 40), 1.0)

        painter.strokePath(path, border_pen)

        center_y = h / 2.0

        # --- Done / Cancelled State ---
        if self.state in ("done", "cancelled"):
            font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
            painter.setFont(font)
            text_col = QColor(245, 245, 250) if self.state == "done" else QColor(252, 165, 165)
            painter.setPen(text_col)
            text_rect = QRectF(14, 0, w - 28, h)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.status_text)
            return

        # --- Audio-Reactive Soundwave Bars (...||||...) ---
        num_bars = 7
        bar_w = 3.2
        spacing = 5.2
        total_w = num_bars * bar_w + (num_bars - 1) * spacing
        start_x = (w - total_w) / 2.0

        for i in range(num_bars):
            bx = start_x + i * (bar_w + spacing)

            # Center bars are naturally taller
            envelope = math.sin((i + 1) / (num_bars + 1) * math.pi)

            if self.state == "recording":
                # Reactive wave bouncing to live microphone amplitude
                idle_wave = 0.5 + 0.5 * math.sin(self._bars_phase + i * 0.9)
                mic_boost = self._current_volume * 18.0 * envelope
                bar_h = 4.0 + 8.0 * envelope * idle_wave + mic_boost
                alpha = int(180 + 75 * min(1.0, idle_wave + self._current_volume))
                bar_color = QColor(255, 255, 255, min(255, alpha))
            else:
                # Transcribing shimmer (violet / pink pulse)
                wave_factor = 0.5 + 0.5 * math.sin(self._bars_phase * 1.6 + i * 1.1)
                bar_h = 4.0 + 13.0 * envelope * wave_factor
                # Color shifts across violet and fuchsia
                r = int(147 + 50 * wave_factor)
                g = int(80 + 40 * envelope)
                b = int(245 + 10 * wave_factor)
                bar_color = QColor(r, g, b, int(200 + 55 * wave_factor))

            by = center_y - bar_h / 2.0
            painter.setBrush(bar_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 1.6, 1.6)
