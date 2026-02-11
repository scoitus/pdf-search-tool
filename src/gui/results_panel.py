"""Results panel with tree view, expandable snippets, and filter."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QLabel, QMenu, QApplication, QTextEdit,
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QAction, QFont, QColor

from models.search_result import FileResult, MatchContext

# Custom data roles
ROLE_FILE_PATH = Qt.ItemDataRole.UserRole
ROLE_PAGE_NUM = Qt.ItemDataRole.UserRole + 1
ROLE_EXTENDED_CTX = Qt.ItemDataRole.UserRole + 2
ROLE_MATCH_TEXT = Qt.ItemDataRole.UserRole + 3
ROLE_IS_SNIPPET = Qt.ItemDataRole.UserRole + 4


class SnippetWidget(QTextEdit):
    """Read-only text widget for displaying expanded match snippets."""

    def __init__(self, extended_context: str, match_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("snippetView")
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        # Build highlighted HTML content
        html = self._highlight_match(extended_context, match_text)
        self.setHtml(html)

        # Size to content, capped at a max height
        doc = self.document()
        doc.setTextWidth(self.viewport().width() or 500)
        content_height = int(doc.size().height()) + 16
        self.setFixedHeight(min(content_height, 180))

    def _highlight_match(self, context: str, match_text: str) -> str:
        """Highlight the match term within the extended context."""
        import html as html_mod

        escaped_ctx = html_mod.escape(context)
        escaped_match = html_mod.escape(match_text)

        # Case-insensitive replacement for highlighting
        import re
        pattern = re.escape(escaped_match)
        highlighted = re.sub(
            pattern,
            lambda m: (
                f'<span style="background-color: #0a84ff; color: white; '
                f'padding: 1px 3px; border-radius: 3px; font-weight: 600;">'
                f'{m.group()}</span>'
            ),
            escaped_ctx,
            flags=re.IGNORECASE,
        )

        return (
            f'<div style="font-family: SF Mono, Menlo, Monaco, monospace; '
            f'font-size: 12px; color: #d0d0d0; line-height: 1.5;">'
            f'{highlighted}</div>'
        )


class ResultsPanel(QWidget):
    """Right panel displaying search results in a tree structure."""

    open_pdf_requested = pyqtSignal(str, int)   # file_path, page_number
    reveal_requested = pyqtSignal(str)          # file_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_items: dict[str, QTreeWidgetItem] = {}
        self._expanded_snippets: dict[int, QTreeWidgetItem] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        filter_label = QLabel("Filter results:")
        filter_label.setObjectName("sectionLabel")
        filter_layout.addWidget(filter_label)

        self.filter_input = QLineEdit()
        self.filter_input.setObjectName("resultsFilter")
        self.filter_input.setPlaceholderText("Type to filter displayed results...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_input)

        layout.addLayout(filter_layout)

        # Hint label
        self.hint_label = QLabel("Click a match to expand snippet. Double-click to open in Preview.")
        self.hint_label.setObjectName("sectionLabel")
        self.hint_label.setStyleSheet("color: #6e6e73; font-size: 11px; padding: 0;")
        layout.addWidget(self.hint_label)

        # Results tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Location", "Page", "Match Context"])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 50)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

        # Summary label
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("sectionLabel")
        layout.addWidget(self.summary_label)

    def add_file_result(self, result: FileResult):
        """Add results for a file incrementally."""
        if not result.matches and not result.error:
            return

        file_item = QTreeWidgetItem(self.tree)
        match_count = len(result.matches)
        file_item.setText(0, f"{result.file_name} ({match_count} match{'es' if match_count != 1 else ''})")
        file_item.setData(0, ROLE_FILE_PATH, result.file_path)

        # Bold font for file entries
        font = file_item.font(0)
        font.setBold(True)
        file_item.setFont(0, font)

        # Color the file header
        file_item.setForeground(0, QColor("#0a84ff"))

        if result.error:
            error_item = QTreeWidgetItem(file_item)
            error_item.setText(2, f"Error: {result.error}")
            error_item.setForeground(2, QColor("#ff453a"))
        else:
            for match in result.matches:
                match_item = QTreeWidgetItem(file_item)
                match_item.setText(1, str(match.page_number))
                context = f"{match.context_before} [{match.match_text}] {match.context_after}"
                match_item.setText(2, context)
                match_item.setData(0, ROLE_FILE_PATH, result.file_path)
                match_item.setData(0, ROLE_PAGE_NUM, match.page_number)
                match_item.setData(0, ROLE_EXTENDED_CTX, match.extended_context)
                match_item.setData(0, ROLE_MATCH_TEXT, match.match_text)
                match_item.setToolTip(2, "Click to expand snippet")

                # Subtle color for page numbers
                match_item.setForeground(1, QColor("#8e8e93"))

        file_item.setExpanded(True)
        self._file_items[result.file_path] = file_item

    def clear_results(self):
        """Clear all results for a new search."""
        self._collapse_all_snippets()
        self.tree.clear()
        self._file_items.clear()
        self._expanded_snippets.clear()
        self.summary_label.setText("")
        self.filter_input.clear()

    def set_summary(self, files_searched: int, files_matched: int,
                    total_matches: int, elapsed: float):
        """Update the summary label."""
        self.summary_label.setText(
            f"{files_searched} files searched  |  "
            f"{files_matched} files matched  |  "
            f"{total_matches} total matches  |  "
            f"{elapsed:.1f}s"
        )

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Toggle expanded snippet on single click of a match item."""
        extended_ctx = item.data(0, ROLE_EXTENDED_CTX)
        match_text = item.data(0, ROLE_MATCH_TEXT)
        if not extended_ctx:
            return  # File header or non-match item

        item_id = id(item)

        if item_id in self._expanded_snippets:
            # Collapse: remove the snippet child
            self._collapse_snippet(item, item_id)
        else:
            # Expand: add a snippet child with the widget
            self._expand_snippet(item, item_id, extended_ctx, match_text)

    def _expand_snippet(self, parent_item: QTreeWidgetItem, item_id: int,
                        extended_ctx: str, match_text: str):
        """Add an expandable snippet widget as a child of the match item."""
        snippet_item = QTreeWidgetItem(parent_item)
        snippet_item.setData(0, ROLE_IS_SNIPPET, True)

        # Create the snippet widget
        snippet_widget = SnippetWidget(extended_ctx, match_text)

        # Set the widget in the tree (spans all columns via column 0)
        self.tree.setItemWidget(snippet_item, 2, snippet_widget)

        # Make columns 0 and 1 empty for the snippet row
        snippet_item.setText(0, "")
        snippet_item.setText(1, "")

        parent_item.setExpanded(True)
        self._expanded_snippets[item_id] = snippet_item

    def _collapse_snippet(self, parent_item: QTreeWidgetItem, item_id: int):
        """Remove a snippet child item."""
        snippet_item = self._expanded_snippets.pop(item_id, None)
        if snippet_item:
            idx = parent_item.indexOfChild(snippet_item)
            if idx >= 0:
                parent_item.takeChild(idx)

    def _collapse_all_snippets(self):
        """Collapse all expanded snippets."""
        for item_id, snippet_item in list(self._expanded_snippets.items()):
            parent = snippet_item.parent()
            if parent:
                idx = parent.indexOfChild(snippet_item)
                if idx >= 0:
                    parent.takeChild(idx)
        self._expanded_snippets.clear()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Open PDF at the matched page when double-clicking a match item."""
        # Don't act on snippet items
        if item.data(0, ROLE_IS_SNIPPET):
            return

        file_path = item.data(0, ROLE_FILE_PATH)
        page_number = item.data(0, ROLE_PAGE_NUM)
        if file_path and page_number:
            self.open_pdf_requested.emit(file_path, page_number)
        elif file_path:
            # Clicked on a file header — open page 1
            self.open_pdf_requested.emit(file_path, 1)

    def _show_context_menu(self, position):
        """Show right-click context menu."""
        item = self.tree.itemAt(position)
        if not item:
            return

        # Don't show menu for snippet items
        if item.data(0, ROLE_IS_SNIPPET):
            return

        file_path = item.data(0, ROLE_FILE_PATH)
        page_number = item.data(0, ROLE_PAGE_NUM)
        if not file_path:
            return

        menu = QMenu(self)

        open_action = QAction("Open in Preview", self)
        open_action.triggered.connect(
            lambda: self.open_pdf_requested.emit(file_path, page_number or 1)
        )
        menu.addAction(open_action)

        reveal_action = QAction("Reveal in Finder", self)
        reveal_action.triggered.connect(
            lambda: self.reveal_requested.emit(file_path)
        )
        menu.addAction(reveal_action)

        menu.addSeparator()

        copy_path_action = QAction("Copy File Path", self)
        copy_path_action.triggered.connect(
            lambda: QApplication.clipboard().setText(file_path)
        )
        menu.addAction(copy_path_action)

        # Copy extended context if available
        extended_ctx = item.data(0, ROLE_EXTENDED_CTX)
        if extended_ctx:
            copy_snippet_action = QAction("Copy Full Snippet", self)
            copy_snippet_action.triggered.connect(
                lambda: QApplication.clipboard().setText(extended_ctx)
            )
            menu.addAction(copy_snippet_action)
        elif page_number:
            copy_match_action = QAction("Copy Match Text", self)
            match_text = item.text(2)
            copy_match_action.triggered.connect(
                lambda: QApplication.clipboard().setText(match_text)
            )
            menu.addAction(copy_match_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _apply_filter(self, text: str):
        """Filter displayed results by text."""
        text_lower = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            file_item = self.tree.topLevelItem(i)
            file_visible = False

            for j in range(file_item.childCount()):
                match_item = file_item.child(j)
                # Skip snippet items in filtering
                if match_item.data(0, ROLE_IS_SNIPPET):
                    continue
                match_text = match_item.text(2).lower()
                visible = not text or text_lower in match_text
                match_item.setHidden(not visible)

                # Also hide/show any snippet children of this match
                for k in range(match_item.childCount()):
                    match_item.child(k).setHidden(not visible)

                if visible:
                    file_visible = True

            # Show file if any child matches, or if filter matches filename
            if not text or text_lower in file_item.text(0).lower():
                file_visible = True

            file_item.setHidden(not file_visible)
