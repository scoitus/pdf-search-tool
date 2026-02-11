"""Multi-folder selector widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QFileDialog, QListWidgetItem,
)
from PyQt6.QtCore import pyqtSignal


class FolderListWidget(QWidget):
    """Widget for managing a list of folders to search."""

    folders_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(120)
        self.list_widget.setToolTip("Folders to search for PDF files")
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self.add_btn = QPushButton("+")
        self.add_btn.setObjectName("addFolderButton")
        self.add_btn.setToolTip("Add folder")
        self.add_btn.clicked.connect(self._add_folder)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("-")
        self.remove_btn.setObjectName("removeFolderButton")
        self.remove_btn.setToolTip("Remove selected folder")
        self.remove_btn.clicked.connect(self._remove_folder)
        btn_layout.addWidget(self.remove_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder to search"
        )
        if folder:
            # Avoid duplicates
            existing = self.get_folders()
            if folder not in existing:
                self.list_widget.addItem(folder)
                self.folders_changed.emit()

    def _remove_folder(self):
        current = self.list_widget.currentRow()
        if current >= 0:
            self.list_widget.takeItem(current)
            self.folders_changed.emit()

    def get_folders(self) -> list[str]:
        """Return all folder paths."""
        return [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]

    def set_folders(self, folders: list[str]):
        """Set the folder list (used when loading profiles)."""
        self.list_widget.clear()
        for folder in folders:
            self.list_widget.addItem(folder)
        self.folders_changed.emit()
