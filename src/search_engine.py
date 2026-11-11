import os
import re
import threading
from pathlib import Path

import fitz  # PyMuPDF

from models.search_result import MatchContext, FileResult, SearchResults


# MuPDF is not safe to use from two threads at once. The search worker and
# the preview renderer (GUI thread) both take this lock around PDF calls.
PDF_LOCK = threading.Lock()


class SearchEngine:
    """Extracts text from PDFs and applies search logic."""

    CONTEXT_CHARS = 80
    EXTENDED_CONTEXT_CHARS = 300

    def search_file(self, file_path: str, query: str,
                    mode: str = "plain", case_sensitive: bool = False) -> FileResult:
        """Search a single PDF file. Returns FileResult with all matches."""
        result = FileResult(
            file_path=file_path,
            file_name=os.path.basename(file_path),
        )
        try:
            with PDF_LOCK:
                doc = fitz.open(file_path)
                result.total_pages = len(doc)
        except Exception as e:
            result.error = str(e)
            return result

        for page_idx in range(result.total_pages):
            # Lock per page so a preview render never waits on a whole file.
            with PDF_LOCK:
                text = doc[page_idx].get_text()
            if not text:
                continue

            spans = self._find_matches(text, query, mode, case_sensitive)
            for start, end in spans:
                before, after = self._extract_context(text, start, end)
                ext_before, ext_after = self._extract_context(
                    text, start, end, self.EXTENDED_CONTEXT_CHARS
                )
                extended = f"{ext_before}{text[start:end]}{ext_after}"
                result.matches.append(MatchContext(
                    page_number=page_idx + 1,
                    match_text=text[start:end],
                    context_before=before,
                    context_after=after,
                    char_offset=start,
                    extended_context=extended,
                ))

        with PDF_LOCK:
            doc.close()
        return result

    def search_folder(self, folder_path: str, query: str,
                      mode: str = "plain", case_sensitive: bool = False,
                      recursive: bool = True,
                      progress_callback=None) -> list[FileResult]:
        """Search all PDFs in a folder.

        progress_callback(current, total, filename) is called per file.
        """
        pdf_files = self.find_pdfs(folder_path, recursive)
        results = []

        for i, pdf_path in enumerate(pdf_files):
            if progress_callback:
                progress_callback(i + 1, len(pdf_files), os.path.basename(pdf_path))
            result = self.search_file(pdf_path, query, mode, case_sensitive)
            results.append(result)

        return results

    def find_pdfs(self, folder_path: str, recursive: bool = True) -> list[str]:
        """Find all PDF files in a folder."""
        folder = Path(folder_path)
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdfs = sorted(str(p) for p in folder.glob(pattern) if p.is_file())
        return pdfs

    def _find_matches(self, text: str, query: str,
                      mode: str, case_sensitive: bool) -> list[tuple[int, int]]:
        """Find all match spans in text. Returns list of (start, end) tuples."""
        if mode == "plain":
            return self._find_plain(text, query, case_sensitive)
        elif mode == "regex":
            return self._find_regex(text, query, case_sensitive)
        elif mode == "boolean":
            # Boolean mode is handled by the BooleanParser (imported when needed)
            from boolean_parser import BooleanParser
            parser = BooleanParser()
            return parser.find_matches(text, query, case_sensitive)
        return []

    def _find_plain(self, text: str, query: str,
                    case_sensitive: bool) -> list[tuple[int, int]]:
        """Plain text search returning (start, end) spans."""
        spans = []
        search_text = text if case_sensitive else text.lower()
        search_query = query if case_sensitive else query.lower()
        if not search_query:
            return spans

        start = 0
        while True:
            idx = search_text.find(search_query, start)
            if idx == -1:
                break
            spans.append((idx, idx + len(search_query)))
            start = idx + 1  # Allow overlapping matches

        return spans

    def _find_regex(self, text: str, query: str,
                    case_sensitive: bool) -> list[tuple[int, int]]:
        """Regex search returning (start, end) spans."""
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return [(m.start(), m.end()) for m in re.finditer(query, text, flags)]
        except re.error:
            return []

    def _extract_context(self, text: str, start: int, end: int,
                         ctx_size: int | None = None) -> tuple[str, str]:
        """Extract surrounding context for a match span."""
        ctx = ctx_size if ctx_size is not None else self.CONTEXT_CHARS

        # Context before
        ctx_start = max(0, start - ctx)
        before = text[ctx_start:start]
        # Trim to word boundary if we're not at the start of the text
        if ctx_start > 0:
            space_idx = before.find(" ")
            if space_idx != -1:
                before = before[space_idx + 1:]
            before = "..." + before

        # Context after
        ctx_end = min(len(text), end + ctx)
        after = text[end:ctx_end]
        # Trim to word boundary if we're not at the end of the text
        if ctx_end < len(text):
            space_idx = after.rfind(" ")
            if space_idx != -1:
                after = after[:space_idx]
            after = after + "..."

        # Clean up whitespace
        before = " ".join(before.split())
        after = " ".join(after.split())

        return before, after
