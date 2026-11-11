"""Sidebar: where to search (sources, subfolders, recent folders)."""

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from gui.folder_list_widget import FolderListWidget
from gui.recent_folders_widget import RecentFoldersWidget


class SearchPanel(QWidget):
    """Left sidebar with the list of folders/files to search."""

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(230)
        self.setMaximumWidth(380)
        self.settings = settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        sources_label = QLabel("SEARCH IN")
        sources_label.setObjectName("sectionLabel")
        layout.addWidget(sources_label)

        self.folder_list = FolderListWidget()
        layout.addWidget(self.folder_list, 3)

        self.recursive_cb = QCheckBox("Include subfolders")
        self.recursive_cb.setChecked(True)
        layout.addWidget(self.recursive_cb)

        layout.addSpacing(8)

        self.recent_label = QLabel("RECENT FOLDERS")
        self.recent_label.setObjectName("sectionLabel")
        layout.addWidget(self.recent_label)

        self.recent_folders = RecentFoldersWidget(self.settings)
        self.recent_folders.folder_activated.connect(self.folder_list.add_folder)
        layout.addWidget(self.recent_folders, 2)

    def set_recursive(self, value: bool):
        self.recursive_cb.setChecked(value)
