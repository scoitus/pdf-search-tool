"""Recently searched folders panel."""

import os

from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

MAX_RECENT_FOLDERS = 10
SETTINGS_KEY = "recentFolders"


class RecentFoldersWidget(QWidget):
    """List of recently searched folders. Double-click or Enter to use."""

    folder_activated = pyqtSignal(str)

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._setup_ui()
        self._reload()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(120)
        self.list_widget.setToolTip(
            "Recently searched folders — double-click to add"
        )
        self.list_widget.itemActivated.connect(self._on_activate)
        layout.addWidget(self.list_widget)

    def _reload(self):
        self.list_widget.clear()
        for path in self.get_recent():
            item = QListWidgetItem(self._display_name(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.list_widget.addItem(item)

    @staticmethod
    def _display_name(path: str) -> str:
        base = os.path.basename(path.rstrip("/")) or path
        return base

    def _on_activate(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.folder_activated.emit(path)

    def get_recent(self) -> list[str]:
        """Return saved recent folders, most-recent first."""
        value = self.settings.value(SETTINGS_KEY, [])
        if isinstance(value, str):
            value = [value]
        return [p for p in (value or []) if isinstance(p, str)]

    def record_folders(self, folders: list[str]):
        """Move/insert folder paths to the front of the recent list and persist.

        Non-directory paths (individual files) are ignored so this list stays
        focused on folders, as the RECENT feature was originally specified.
        """
        existing = self.get_recent()
        # Newest items go first; later folders in the input take priority
        merged: list[str] = []
        seen: set[str] = set()
        for path in list(folders) + existing:
            if not path or path in seen:
                continue
            # Only record directories; skip individual files.
            if not os.path.isdir(path):
                continue
            merged.append(path)
            seen.add(path)
            if len(merged) >= MAX_RECENT_FOLDERS:
                break
        self.settings.setValue(SETTINGS_KEY, merged)
        self._reload()
