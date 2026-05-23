"""Search input panel with query, mode, folders, and action buttons."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QRadioButton, QCheckBox, QPushButton, QButtonGroup,
)
from PyQt6.QtCore import pyqtSignal, Qt, QSettings

from gui.folder_list_widget import FolderListWidget
from gui.recent_folders_widget import RecentFoldersWidget


class SearchPanel(QWidget):
    """Left panel with all search configuration controls."""

    search_requested = pyqtSignal(str, str, bool, list, bool)
    # query, mode, case_sensitive, folders, recursive
    cancel_requested = pyqtSignal()

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.setObjectName("searchPanel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        self.settings = settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- Search term ---
        search_label = QLabel("Search")
        search_label.setObjectName("sectionLabel")
        layout.addWidget(search_label)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search term or expression...")
        self.query_input.returnPressed.connect(self._on_search)
        self.query_input.textChanged.connect(self._update_search_enabled)
        layout.addWidget(self.query_input)

        # --- Search mode ---
        mode_label = QLabel("Mode")
        mode_label.setObjectName("sectionLabel")
        layout.addWidget(mode_label)

        self.mode_group = QButtonGroup(self)
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(12)

        self.plain_radio = QRadioButton("Plain")
        self.plain_radio.setChecked(True)
        self.plain_radio.setToolTip("Case-insensitive text search")
        self.mode_group.addButton(self.plain_radio)
        mode_layout.addWidget(self.plain_radio)

        self.regex_radio = QRadioButton("Regex")
        self.regex_radio.setToolTip("Regular expression search")
        self.mode_group.addButton(self.regex_radio)
        mode_layout.addWidget(self.regex_radio)

        self.boolean_radio = QRadioButton("Boolean")
        self.boolean_radio.setToolTip("AND / OR / NOT with parentheses")
        self.mode_group.addButton(self.boolean_radio)
        mode_layout.addWidget(self.boolean_radio)

        layout.addLayout(mode_layout)

        # --- Options ---
        self.case_sensitive_cb = QCheckBox("Case sensitive")
        layout.addWidget(self.case_sensitive_cb)

        # --- Sources (folders and/or individual files) ---
        folders_label = QLabel("Sources")
        folders_label.setObjectName("sectionLabel")
        layout.addWidget(folders_label)

        self.folder_list = FolderListWidget()
        self.folder_list.folders_changed.connect(self._update_search_enabled)
        layout.addWidget(self.folder_list)

        self.recursive_cb = QCheckBox("Search subdirectories")
        self.recursive_cb.setChecked(True)
        layout.addWidget(self.recursive_cb)

        # --- Recent folders ---
        recent_label = QLabel("Recent")
        recent_label.setObjectName("sectionLabel")
        layout.addWidget(recent_label)

        self.recent_folders = RecentFoldersWidget(self.settings)
        self.recent_folders.folder_activated.connect(self.folder_list.add_folder)
        layout.addWidget(self.recent_folders)

        # --- Spacer ---
        layout.addStretch()

        # --- Buttons ---
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("searchButton")
        self.search_btn.clicked.connect(self._on_search)
        self.search_btn.setEnabled(False)
        self.search_btn.setToolTip("Enter a query and add at least one source")
        layout.addWidget(self.search_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        self.cancel_btn.setVisible(False)
        layout.addWidget(self.cancel_btn)

    def _on_search(self):
        query = self.query_input.text().strip()
        if not query:
            return
        folders = self.folder_list.get_folders()
        if not folders:
            return

        mode = self.get_mode()
        case_sensitive = self.case_sensitive_cb.isChecked()
        recursive = self.recursive_cb.isChecked()

        self.search_requested.emit(query, mode, case_sensitive, folders, recursive)

    def get_mode(self) -> str:
        if self.regex_radio.isChecked():
            return "regex"
        if self.boolean_radio.isChecked():
            return "boolean"
        return "plain"

    def set_searching(self, searching: bool):
        """Toggle UI between searching and idle states."""
        self._searching = searching
        self.search_btn.setVisible(not searching)
        self.cancel_btn.setVisible(searching)
        self.query_input.setEnabled(not searching)
        self._update_search_enabled()

    def _update_search_enabled(self):
        """Enable Search only when there's a query and at least one source."""
        if getattr(self, "_searching", False):
            self.search_btn.setEnabled(False)
            return
        has_query = bool(self.query_input.text().strip())
        has_sources = bool(self.folder_list.get_folders())
        self.search_btn.setEnabled(has_query and has_sources)
        if not has_query:
            self.search_btn.setToolTip("Enter a search query")
        elif not has_sources:
            self.search_btn.setToolTip("Add a folder or file to search")
        else:
            self.search_btn.setToolTip("")

    def get_query(self) -> str:
        return self.query_input.text().strip()

    def set_query(self, query: str):
        self.query_input.setText(query)

    def set_mode(self, mode: str):
        if mode == "regex":
            self.regex_radio.setChecked(True)
        elif mode == "boolean":
            self.boolean_radio.setChecked(True)
        else:
            self.plain_radio.setChecked(True)

    def set_case_sensitive(self, value: bool):
        self.case_sensitive_cb.setChecked(value)

    def set_recursive(self, value: bool):
        self.recursive_cb.setChecked(value)
