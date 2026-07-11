#ACTUAL APPLICATION ENTRY POINT
import sys
from PySide6.QtWidgets import QApplication
from bootstrap.updater import check_and_update, restart, force_sync
from gui.fairy_window import FairyWindow
from gui.bridge import FairyWorker
from gui.hotkeys import start_mute_hotkey_listener, start_clear_hotkey_listener, start_hide_icon_listener

def main():
    if "--force-sync" in sys.argv: #Force sync desperate measure
        if force_sync():
            restart()
    elif check_and_update():
        restart()

    qt_app = QApplication(sys.argv)
    window = FairyWindow()
    window.show()

    worker = FairyWorker() #Initialize Fairy (instance of a program)
    worker.start() #Start the program up
    worker.finished.connect(qt_app.quit) #Quit the application
    
    #Asynchronous threads
    start_mute_hotkey_listener()
    start_clear_hotkey_listener()
    start_hide_icon_listener()

    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()