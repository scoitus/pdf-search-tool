"""Background search thread for non-blocking PDF search."""

import os
import time

from PyQt6.QtCore import QThread, pyqtSignal

from search_engine import SearchEngine
from models.search_result import FileResult, SearchResults


class SearchWorker(QThread):
    """Runs PDF search in a background thread."""

    progress = pyqtSignal(int, int, str)        # current, total, filename
    file_completed = pyqtSignal(object)          # FileResult (with matches)
    search_finished = pyqtSignal(object)         # SearchResults
    error_occurred = pyqtSignal(str)             # error message

    def __init__(self, engine: SearchEngine, folders: list[str],
                 query: str, mode: str, case_sensitive: bool,
                 recursive: bool):
        super().__init__()
        self.engine = engine
        self.folders = folders
        self.query = query
        self.mode = mode
        self.case_sensitive = case_sensitive
        self.recursive = recursive
        self._cancelled = False

    def run(self):
        start_time = time.time()
        all_results: list[FileResult] = []

        # Gather all PDF files across all folders
        pdf_files: list[str] = []
        for folder in self.folders:
            try:
                pdf_files.extend(self.engine.find_pdfs(folder, self.recursive))
            except Exception as e:
                self.error_occurred.emit(f"Error scanning {folder}: {e}")

        total = len(pdf_files)
        files_with_matches = 0
        total_matches = 0

        for i, pdf_path in enumerate(pdf_files):
            if self._cancelled:
                break

            self.progress.emit(i + 1, total, os.path.basename(pdf_path))

            try:
                result = self.engine.search_file(
                    pdf_path, self.query, self.mode, self.case_sensitive
                )
                if result.matches:
                    files_with_matches += 1
                    total_matches += len(result.matches)
                    self.file_completed.emit(result)
                all_results.append(result)
            except Exception as e:
                err_result = FileResult(
                    file_path=pdf_path,
                    file_name=os.path.basename(pdf_path),
                    error=str(e),
                )
                all_results.append(err_result)
                self.file_completed.emit(err_result)

        elapsed = time.time() - start_time

        search_results = SearchResults(
            query=self.query,
            files_searched=len(all_results),
            files_with_matches=files_with_matches,
            total_matches=total_matches,
            file_results=all_results,
            elapsed_seconds=elapsed,
        )
        self.search_finished.emit(search_results)

    def cancel(self):
        self._cancelled = True
