import sys
from PyQt6.QtWidgets import QApplication
from ui import AutoClickerWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Auto Clicker")
    app.setDesktopFileName("Auto Clicker.desktop")

    window = AutoClickerWindow()
    window.show()

    sys.exit(app.exec())
