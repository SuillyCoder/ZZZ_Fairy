#PySide6 Imports
from PySide6.QtWidgets import QWidget #Widget import
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation #Animation-related imports
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QPen #Drawing related imports

#Create a class instance of an orb widget
class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._pulse = 0.0
        self._rotation = 0.0

        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._tick)
        self._idle_timer.start(16)  # ~60fps

        self._pulse_anim = QPropertyAnimation(self, b"pulse")
        self._pulse_anim.setDuration(280)

    def _tick(self):
        self._rotation = (self._rotation + 0.6) % 360
        self.update()

    def getPulse(self): return self._pulse
    def setPulse(self, v):
        self._pulse = v
        self.update()
    pulse = Property(float, getPulse, setPulse)

    def set_speaking(self, is_speaking: bool):
        self._pulse_anim.stop()
        self._pulse_anim.setStartValue(self._pulse)
        self._pulse_anim.setEndValue(1.0 if is_speaking else 0.0)
        self._pulse_anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        base_r = min(self.width(), self.height()) * 0.42
        boost = 1.0 + 0.12 * self._pulse

        glow = QRadialGradient(cx, cy, base_r * 1.6 * boost)
        glow.setColorAt(0.0, QColor(120, 180, 255, int(160 * (0.4 + 0.6 * self._pulse))))
        glow.setColorAt(1.0, QColor(120, 180, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(cx - base_r*1.6, cy - base_r*1.6, base_r*3.2, base_r*3.2)

        for i, color in enumerate([QColor(20,40,110), QColor(160,200,255), QColor(60,120,230)]):
            r = base_r * (1.0 - i*0.28) * boost
            p.setPen(QPen(color, 3)); p.setBrush(Qt.NoBrush)
            p.drawEllipse(cx - r, cy - r, r*2, r*2)

        dot_r = base_r * 0.10
        p.setBrush(QColor(255,255,255)); p.setPen(Qt.NoPen)
        p.drawEllipse(cx - dot_r*0.3, cy + dot_r*0.6, dot_r, dot_r)