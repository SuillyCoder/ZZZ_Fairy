from PySide6.QtCore import QObject, Signal, QThread #PySide6 imports

class FairyBridge(QObject): #Create bridge class for Fairy's voice to sync and bridge to UI
    speaking_started = Signal()
    speaking_stopped = Signal()
    mute_toggled = Signal(bool) #Boolean signal to toggle on/off "mute button"

    def __init__ (self):
        super().__init__()
        self.muted = False #Open Fairy up for listening for input

    def toggle_mute(self): #Asynchronous function to toggle being muted on and off
        self.muted = not self.muted #Flip the status
        self.mute_toggled.emit(self.muted) #Fire toggle
        return self.muted #Return muted status

fairy_bridge = FairyBridge() #Bridge import

class FairyWorker(QThread):
    def run(self):
        import main_wrapped #Import the wrapped main function
        main_wrapped.run() #Run it