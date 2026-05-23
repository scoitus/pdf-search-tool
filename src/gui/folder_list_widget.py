"""Multi-source selector widget — folders and individual PDF files."""

import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QStyle, QVBoxLayout, QWidget,
)


class FolderListWidget(QWidget):
    """Manages a list of search sources: folders and/or individual PDF files."""

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
        self.list_widget.setToolTip("Folders and PDF files to search")
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self.add_folder_btn = QPushButton("+ Folder")
        self.add_folder_btn.setObjectName("addSourceButton")
        self.add_folder_btn.setToolTip("Add a folder to search")
        self.add_folder_btn.clicked.connect(self._add_folder)
        btn_layout.addWidget(self.add_folder_btn)

        self.add_file_btn = QPushButton("+ File")
        self.add_file_btn.setObjectName("addSourceButton")
        self.add_file_btn.setToolTip("Add an individual PDF file to search")
        self.add_file_btn.clicked.connect(self._add_file)
        btn_layout.addWidget(self.add_file_btn)

        self.remove_btn = QPushButton("−")
        self.remove_btn.setObjectName("removeFolderButton")
        self.remove_btn.setToolTip("Remove the selected item")
        self.remove_btn.clicked.connect(self._remove_item)
        btn_layout.addWidget(self.remove_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # --- icon helpers ---

    def _folder_icon(self):
        return self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)

    def _file_icon(self):
        return self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    # --- handlers ---

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder to search"
        )
        if folder:
            self._append_path(folder, emit=True)

    def _add_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF file(s) to search",
            filter="PDF files (*.pdf)",
        )
        if not files:
            return
        added = False
        for path in files:
            added = self._append_path(path, emit=False) or added
        if added:
            self.folders_changed.emit()

    def _remove_item(self):
        current = self.list_widget.currentRow()
        if current >= 0:
            self.list_widget.takeItem(current)
            self.folders_changed.emit()

    # --- internal helpers ---

    def _append_path(self, path: str, emit: bool) -> bool:
        """Append a path with an appropriate icon. Returns True if added."""
        if not path or path in self.get_folders():
            return False
        item = QListWidgetItem(path)
        if os.path.isdir(path):
            item.setIcon(self._folder_icon())
        else:
            item.setIcon(self._file_icon())
        self.list_widget.addItem(item)
        if emit:
            self.folders_changed.emit()
        return True

    # --- public API (names preserved for backward compatibility) ---

    def get_folders(self) -> list[str]:
        """Return all source paths (both folders and individual files)."""
        return [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]

    def set_folders(self, folders: list[str]):
        """Replace the source list (used when loading profiles)."""
        self.list_widget.clear()
        for path in folders:
            self._append_path(path, emit=False)
        self.folders_changed.emit()

    def add_folder(self, folder: str):
        """Append a folder or file path if not already present."""
        self._append_path(folder, emit=True)
