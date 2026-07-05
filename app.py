#ACTUAL APPLICATION ENTRY POINT
import sys
from PySide6.QtWidgets import QApplication
from bootstrap.updater import check_and_update, restart
from gui.fairy_window import FairyWindow
from gui.bridge import FairyWorker

def main():
    if check_and_update():
        restart()

    qt_app = QApplication(sys.argv)
    window = FairyWindow()
    window.show()

    worker = FairyWorker() #Initialize Fairy (instance of a program)
    worker.start() #Start the program up
    worker.finished.connect(qt_app.quit) #Quit the application

    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()