#PySide6 Imports
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from .orb_widget import OrbWidget
from .bridge import fairy_bridge

class FairyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(220, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.orb = OrbWidget(self)
        layout.addWidget(self.orb)

        fairy_bridge.speaking_started.connect(lambda: self.orb.set_speaking(True))
        fairy_bridge.speaking_stopped.connect(lambda: self.orb.set_speaking(False))
        fairy_bridge.toggle_visibility_requested.connect(self.toggle_visibility)

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())