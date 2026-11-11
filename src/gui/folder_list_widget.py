"""Multi-source selector widget — folders and individual PDF files."""

import os

from PyQt6.QtCore import QFileInfo, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeySequence, QPainter, QShortcut
from PyQt6.QtWidgets import (
    QFileDialog, QFileIconProvider, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from gui.styles import current_theme

ROLE_PATH = Qt.ItemDataRole.UserRole


def display_name(path: str) -> str:
    return os.path.basename(path.rstrip("/")) or path


def short_path(path: str) -> str:
    """Abbreviate the home directory to ~ for friendlier tooltips."""
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home) else path


class _SourceList(QListWidget):
    """List that shows a friendly hint while it is empty."""

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(current_theme().faint))
            painter.drawText(
                self.viewport().rect().adjusted(8, 8, -8, -8),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                | Qt.TextFlag.TextWordWrap,
                "Add a folder or PDF,\nor drop them anywhere\nin this window",
            )


class FolderListWidget(QWidget):
    """Manages a list of search sources: folders and/or individual PDF files."""

    folders_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icons = QFileIconProvider()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.list_widget = _SourceList()
        self.list_widget.setMinimumHeight(90)
        self.list_widget.itemSelectionChanged.connect(self._update_remove_enabled)
        layout.addWidget(self.list_widget, 1)

        for key in (QKeySequence.StandardKey.Delete, QKeySequence("Backspace")):
            shortcut = QShortcut(key, self.list_widget)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(self._remove_item)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.add_folder_btn = QPushButton("+ Folder")
        self.add_folder_btn.setObjectName("addSourceButton")
        self.add_folder_btn.setToolTip("Add a folder to search")
        self.add_folder_btn.clicked.connect(self._add_folder)
        btn_layout.addWidget(self.add_folder_btn)

        self.add_file_btn = QPushButton("+ PDF")
        self.add_file_btn.setObjectName("addSourceButton")
        self.add_file_btn.setToolTip("Add individual PDF files to search")
        self.add_file_btn.clicked.connect(self._add_file)
        btn_layout.addWidget(self.add_file_btn)

        btn_layout.addStretch()

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setObjectName("removeSourceButton")
        self.remove_btn.setToolTip("Remove the selected item from the list")
        self.remove_btn.clicked.connect(self._remove_item)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)

        layout.addLayout(btn_layout)

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
        self.add_paths(files)

    def _remove_item(self):
        current = self.list_widget.currentRow()
        if current >= 0:
            self.list_widget.takeItem(current)
            self.folders_changed.emit()

    def _update_remove_enabled(self):
        self.remove_btn.setEnabled(bool(self.list_widget.selectedItems()))

    # --- internal helpers ---

    def _append_path(self, path: str, emit: bool) -> bool:
        """Append a path with its Finder icon. Returns True if added."""
        if not path or path in self.get_folders():
            return False
        item = QListWidgetItem(display_name(path))
        item.setData(ROLE_PATH, path)
        item.setToolTip(short_path(path))
        item.setIcon(self._icons.icon(QFileInfo(path)))
        self.list_widget.addItem(item)
        if emit:
            self.folders_changed.emit()
        return True

    # --- public API (names preserved for backward compatibility) ---

    def get_folders(self) -> list[str]:
        """Return all source paths (both folders and individual files)."""
        return [
            self.list_widget.item(i).data(ROLE_PATH)
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

    def add_paths(self, paths: list[str]):
        """Append several paths, emitting a single change signal."""
        added = False
        for path in paths:
            added = self._append_path(path, emit=False) or added
        if added:
            self.folders_changed.emit()
