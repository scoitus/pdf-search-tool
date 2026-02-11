"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QStatusBar, QProgressBar,
    QLabel, QMenuBar, QMenu, QMessageBox,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence

from search_engine import SearchEngine
from profile_manager import ProfileManager
from preview_opener import open_pdf_at_page, reveal_in_finder
from models.search_result import SearchResults, FileResult
from models.search_profile import SearchProfile
from gui.search_panel import SearchPanel
from gui.results_panel import ResultsPanel
from gui.profile_dialog import SaveProfileDialog, LoadProfileDialog
from workers.search_worker import SearchWorker


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.engine = SearchEngine()
        self.profile_manager = ProfileManager()
        self.worker: SearchWorker | None = None
        self.settings = QSettings("CT", "PDFSearchTool")

        self._setup_ui()
        self._setup_menu_bar()
        self._setup_shortcuts()
        self._restore_geometry()

    def _setup_ui(self):
        # Central splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Search panel (left)
        self.search_panel = SearchPanel()
        self.search_panel.search_requested.connect(self._start_search)
        self.search_panel.cancel_requested.connect(self._cancel_search)
        self.splitter.addWidget(self.search_panel)

        # Results panel (right)
        self.results_panel = ResultsPanel()
        self.results_panel.open_pdf_requested.connect(self._open_pdf)
        self.results_panel.reveal_requested.connect(reveal_in_finder)
        self.splitter.addWidget(self.results_panel)

        # Splitter proportions
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([300, 800])

        self.setCentralWidget(self.splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

    def _setup_menu_bar(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Search menu
        search_menu = menu_bar.addMenu("Search")

        new_search_action = QAction("New Search", self)
        new_search_action.setShortcut(QKeySequence("Ctrl+N"))
        new_search_action.triggered.connect(self._new_search)
        search_menu.addAction(new_search_action)

        focus_search_action = QAction("Focus Search Field", self)
        focus_search_action.setShortcut(QKeySequence("Ctrl+F"))
        focus_search_action.triggered.connect(
            lambda: self.search_panel.query_input.setFocus()
        )
        search_menu.addAction(focus_search_action)

        # Profiles menu
        profiles_menu = menu_bar.addMenu("Profiles")

        save_profile_action = QAction("Save Current Search...", self)
        save_profile_action.setShortcut(QKeySequence("Ctrl+S"))
        save_profile_action.triggered.connect(self._save_profile)
        profiles_menu.addAction(save_profile_action)

        load_profile_action = QAction("Load Profile...", self)
        load_profile_action.setShortcut(QKeySequence("Ctrl+O"))
        load_profile_action.triggered.connect(self._load_profile)
        profiles_menu.addAction(load_profile_action)

    def _setup_shortcuts(self):
        pass  # Shortcuts are set via menu actions above

    def _start_search(self, query: str, mode: str, case_sensitive: bool,
                      folders: list[str], recursive: bool):
        """Start a search in a background thread."""
        if self.worker and self.worker.isRunning():
            return

        self.results_panel.clear_results()
        self.search_panel.set_searching(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Searching...")

        self.worker = SearchWorker(
            self.engine, folders, query, mode, case_sensitive, recursive
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.file_completed.connect(self._on_file_completed)
        self.worker.search_finished.connect(self._on_search_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _cancel_search(self):
        """Cancel a running search."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("Cancelling...")

    def _on_progress(self, current: int, total: int, filename: str):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Searching {current}/{total}: {filename}")

    def _on_file_completed(self, result: FileResult):
        self.results_panel.add_file_result(result)

    def _on_search_finished(self, results: SearchResults):
        self.search_panel.set_searching(False)
        self.progress_bar.setVisible(False)

        self.results_panel.set_summary(
            results.files_searched,
            results.files_with_matches,
            results.total_matches,
            results.elapsed_seconds,
        )

        if results.total_matches == 0:
            self.status_label.setText(
                f"No matches found ({results.files_searched} files searched, "
                f"{results.elapsed_seconds:.1f}s)"
            )
        else:
            self.status_label.setText(
                f"{results.total_matches} matches in "
                f"{results.files_with_matches} files "
                f"({results.elapsed_seconds:.1f}s)"
            )

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")

    def _open_pdf(self, file_path: str, page_number: int):
        open_pdf_at_page(file_path, page_number)

    def _new_search(self):
        """Clear and focus for a new search."""
        self.results_panel.clear_results()
        self.search_panel.set_query("")
        self.search_panel.query_input.setFocus()
        self.status_label.setText("Ready")

    def _save_profile(self):
        """Save the current search configuration as a profile."""
        query = self.search_panel.get_query()
        dialog = SaveProfileDialog(self, default_name=query[:30] if query else "")
        if dialog.exec():
            profile = SearchProfile(
                name=dialog.profile_name,
                query=query,
                folders=self.search_panel.folder_list.get_folders(),
                case_sensitive=self.search_panel.case_sensitive_cb.isChecked(),
                search_mode=self.search_panel.get_mode(),
                recursive=self.search_panel.recursive_cb.isChecked(),
            )
            self.profile_manager.save_profile(profile)
            self.status_label.setText(f"Profile '{profile.name}' saved")

    def _load_profile(self):
        """Load a saved profile into the search panel."""
        profiles = self.profile_manager.load_profiles()
        if not profiles:
            QMessageBox.information(
                self, "No Profiles",
                "No saved profiles found. Use Profiles > Save Current Search "
                "to create one."
            )
            return

        dialog = LoadProfileDialog(profiles, self)
        if dialog.exec() and dialog.selected_profile:
            p = dialog.selected_profile
            self.search_panel.set_query(p.query)
            self.search_panel.set_mode(p.search_mode)
            self.search_panel.set_case_sensitive(p.case_sensitive)
            self.search_panel.set_recursive(p.recursive)
            self.search_panel.folder_list.set_folders(p.folders)
            self.profile_manager.update_last_used(p.name)
            self.status_label.setText(f"Profile '{p.name}' loaded")

    def _restore_geometry(self):
        """Restore window geometry from settings."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        splitter_state = self.settings.value("splitter")
        if splitter_state:
            self.splitter.restoreState(splitter_state)

    def closeEvent(self, event):
        """Save window geometry on close."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter", self.splitter.saveState())
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)
        super().closeEvent(event)
