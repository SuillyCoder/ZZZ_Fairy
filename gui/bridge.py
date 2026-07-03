from PySide6.QtCore import QObject, Signal, QThread #PySide6 imports

class FairyBridge(QObject): #Create bridge class for Fairy's voice to sync and bridge to UI
    speaking_started = Signal()
    speaking_stopped = Signal()

fairy_bridge = FairyBridge() #Bridge import

class FairyWorker(QThread):
    def run(self):
        import main_wrapped #Import the wrapped main function
        main_wrapped.run() #Run it