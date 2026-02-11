"""PDF Search Tool — Entry point."""

import sys
import os

# Ensure src directory is on the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow
from gui.styles import MACOS_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Search Tool")
    app.setOrganizationName("CT")
    app.setOrganizationDomain("com.user.pdfsearchtool")

    app.setStyleSheet(MACOS_STYLESHEET)

    window = MainWindow()
    window.setWindowTitle("PDF Search Tool")
    window.resize(1100, 700)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
