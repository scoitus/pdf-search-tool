"""Dialogs for saving and loading search profiles."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton, QListWidgetItem, QMessageBox,
)
from PyQt6.QtCore import Qt

from models.search_profile import SearchProfile
from profile_manager import ProfileManager


class SaveProfileDialog(QDialog):
    """Dialog for saving a search profile."""

    def __init__(self, parent=None, default_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Save Search Profile")
        self.setMinimumWidth(350)
        self.profile_name = ""
        self._setup_ui(default_name)

    def _setup_ui(self, default_name: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        label = QLabel("Profile name:")
        layout.addWidget(label)

        self.name_input = QLineEdit()
        self.name_input.setText(default_name)
        self.name_input.setPlaceholderText("Enter a name for this search profile...")
        self.name_input.selectAll()
        layout.addWidget(self.name_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("searchButton")
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            return
        self.profile_name = name
        self.accept()


class LoadProfileDialog(QDialog):
    """Dialog for loading or deleting a saved profile."""

    def __init__(self, profiles: list[SearchProfile], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Search Profile")
        self.setMinimumSize(450, 350)
        self.profiles = profiles
        self.selected_profile: SearchProfile | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        label = QLabel("Select a profile:")
        layout.addWidget(label)

        self.list_widget = QListWidget()
        for profile in self.profiles:
            item = QListWidgetItem(profile.name)
            detail = f"  {profile.search_mode} | {profile.query}"
            if profile.folders:
                detail += f" | {len(profile.folders)} source(s)"
            item.setToolTip(detail)
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(self._on_load)
        self.list_widget.currentRowChanged.connect(self._update_detail)
        layout.addWidget(self.list_widget)

        # Detail label
        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: #6e6e73; font-size: 12px;")
        layout.addWidget(self.detail_label)

        # Buttons
        btn_layout = QHBoxLayout()

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("color: #ff3b30;")
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        load_btn = QPushButton("Load")
        load_btn.setObjectName("searchButton")
        load_btn.clicked.connect(self._on_load)
        load_btn.setDefault(True)
        btn_layout.addWidget(load_btn)

        layout.addLayout(btn_layout)

    def _update_detail(self, row: int):
        if 0 <= row < len(self.profiles):
            p = self.profiles[row]
            sources = "\n  ".join(p.folders) if p.folders else "(none)"
            self.detail_label.setText(
                f"Query: {p.query}\n"
                f"Mode: {p.search_mode} | "
                f"Case sensitive: {'Yes' if p.case_sensitive else 'No'} | "
                f"Recursive: {'Yes' if p.recursive else 'No'}\n"
                f"Sources:\n  {sources}"
            )
        else:
            self.detail_label.setText("")

    def _on_load(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.profiles):
            self.selected_profile = self.profiles[row]
            self.accept()

    def _on_delete(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.profiles):
            return

        profile = self.profiles[row]
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Delete profile '{profile.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            manager = ProfileManager()
            manager.delete_profile(profile.name)
            self.profiles.pop(row)
            self.list_widget.takeItem(row)
            self.detail_label.setText("")
