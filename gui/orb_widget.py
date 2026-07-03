#PySide6 related imports
import os, time, math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QPixmap

from config import BASE_DIR #import the base directory path
ASSET_DIR = os.path.join(BASE_DIR, "gui", "elements")

# Bottom -> top, matches your numbering exactly
LAYER_FILES = [f"{i}.png" for i in range(2, 9)]
ROTATING_LAYER_INDEX = LAYER_FILES.index("3.png")  # only element 3 spins


#Create a class instance of an orb widget
class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground) #Set a translucent background

        self._layers_raw = [] #Initialize the layer stack for the various elements
        for name in LAYER_FILES: 
            path = os.path.join(ASSET_DIR, name) #Route to the element path
            pix = QPixmap(path) #Displays the corresponding image
            if pix.isNull():
                print(f"[OrbWidget] Warning: couldn't load {path}")
            self._layers_raw.append(pix) #Stack the element onto itself

        loaded = sum(1 for p in self._layers_raw if not p.isNull())
        print(f"[OrbWidget] Loaded {loaded}/{len(self._layers_raw)} layers from {ASSET_DIR}")
        
        self._layers_scaled = []
        self._cached_size = None

        self._elapsed = 0.0
        self._speaking = False
        self._last_time = time.monotonic()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

        # Window dragging — this widget fills the frameless window, so it owns the drag
        self._drag_offset = None
 
    def set_speaking(self, is_speaking: bool): #helper functionto indicate speaking
        self._speaking = is_speaking

    def _tick(self):
        now = time.monotonic()
        self._elapsed += now - self._last_time #calculate the elapsed time
        self._last_time = now
        self.update()

    def _rescale_layers(self):
        size = self.size()
        self._layers_scaled = [
            pix.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation) if not pix.isNull() else pix
            for pix in self._layers_raw
        ]
        self._cached_size = size
        
    def paintEvent(self, event):
        if self._cached_size != self.size():
            self._rescale_layers()

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        cx, cy = self.width() / 2, self.height() / 2

        if self._speaking:
            pulse_speed = 4.0       # faster breathing while talking
            pulse_amplitude = 0.06
            base_scale = 1.08       # a little bigger overall
        else:
            pulse_speed = 0.6       # very slow idle breathing
            pulse_amplitude = 0.02
            base_scale = 1.0

        rotation_deg = (self._elapsed * 18) % 360   # slow constant spin, element 3 only
        pulse = 1.0 + pulse_amplitude * math.sin(self._elapsed * pulse_speed)
        overall_scale = base_scale * pulse

        for i, pix in enumerate(self._layers_scaled):
            if pix.isNull():
                continue
            p.save()
            p.translate(cx, cy)
            if i == ROTATING_LAYER_INDEX:
                p.rotate(rotation_deg)
            p.scale(overall_scale, overall_scale)
            p.drawPixmap(QPointF(-pix.width() / 2, -pix.height() / 2), pix)
            p.restore()

    # ======= HANDLER FUNCTIONS FOR WINDOW DRAGGING ======= #

    def mousePressEvent(self, event): #Detect if the mouse (left click) has been pressed / clicked
        if event.button() == Qt.LeftButton: #If equal to the left button
            self._drag_offset = event.globalPosition().toPoint() - self.window().pos() #Initialize the offset
            event.accept() #Accept instance of the event

    def mouseMoveEvent(self, event): #Detect if the mouse is being moved
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton: #If the offset is set to something
            self.window().move(event.globalPosition().toPoint() - self._drag_offset) #Move the window according to the offset
            event.accept() #Accept instance of the event

    def mouseReleaseEvent(self, event): #Detect if the mouse has been let go of. 
        self._drag_offset = None #Clear the instance of the offset
        event.accept() #Accept instance of the event

    

    
     