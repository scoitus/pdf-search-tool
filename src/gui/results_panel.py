"""Results panel: matches grouped by file, with a floating PDF preview."""

import html
import os

from PyQt6.QtCore import (
    QEvent, QPointF, QRect, QRectF, QSize, Qt, QTimer, pyqtSignal,
)
from PyQt6.QtGui import (
    QAction, QActionGroup, QColor, QFont, QFontMetrics, QPainter, QPolygonF,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QSplitter, QStackedWidget, QStyle, QStyledItemDelegate, QTreeWidget,
    QTreeWidgetItem, QTreeWidgetItemIterator, QVBoxLayout, QWidget,
)

from gui.folder_list_widget import short_path
from gui.page_viewer import PageViewer
from gui.pdf_preview import PdfPreviewPopup
from gui.styles import current_theme
from models.search_result import FileResult, MatchContext, SearchResults

# Custom data roles
ROLE_KIND = Qt.ItemDataRole.UserRole           # "folder" | "file" | "match" | "error"
ROLE_FILE_PATH = Qt.ItemDataRole.UserRole + 1
ROLE_MATCH = Qt.ItemDataRole.UserRole + 2      # MatchContext
ROLE_COUNT = Qt.ItemDataRole.UserRole + 3      # match count (file rows)

HOVER_PREVIEW_DELAY_MS = 350

SORT_OPTIONS = [
    ("found", "Order found"),
    ("name", "Name"),
    ("matches", "Most matches"),
    ("modified", "Recently modified"),
]
GROUP_OPTIONS = [
    ("file", "File"),
    ("folder", "Folder"),
]


class ResultDelegate(QStyledItemDelegate):
    """Paints file headers and match rows (page chip + highlighted snippet)."""

    FOLDER_H = 44
    FILE_H = 48
    MATCH_H = 52
    ERROR_H = 32
    SNIPPET_X = 112   # left edge of snippet text; the preview aligns to it

    show_file_folder = True   # off when results are already grouped by folder

    def sizeHint(self, option, index):
        height = {"folder": self.FOLDER_H, "file": self.FILE_H,
                  "match": self.MATCH_H}.get(index.data(ROLE_KIND), self.ERROR_H)
        return QSize(200, height)

    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme = current_theme()
        kind = index.data(ROLE_KIND)
        if kind == "folder":
            self._paint_folder(painter, option, index, theme)
        elif kind == "file":
            self._paint_file(painter, option, index, theme)
        elif kind == "match":
            self._paint_match(painter, option, index, theme)
        else:
            painter.setPen(QColor(theme.danger))
            painter.drawText(
                option.rect.adjusted(self.SNIPPET_X, 0, -16, 0),
                Qt.AlignmentFlag.AlignVCenter, index.data(Qt.ItemDataRole.DisplayRole),
            )
        painter.restore()

    @staticmethod
    def _paint_chevron(painter, option, theme, cx: float, mid: float):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.faint))
        if option.state & QStyle.StateFlag.State_Open:
            tri = [QPointF(cx - 4.5, mid - 2.5), QPointF(cx + 4.5, mid - 2.5),
                   QPointF(cx, mid + 3.5)]
        else:
            tri = [QPointF(cx - 2.5, mid - 4.5), QPointF(cx - 2.5, mid + 4.5),
                   QPointF(cx + 3.5, mid)]
        painter.drawPolygon(QPolygonF(tri))

    def _paint_folder(self, painter, option, index, theme):
        """Section header: folder path on a tinted band with a file count."""
        r = option.rect.adjusted(12, 14, -12, 0)
        mid = r.center().y()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.hover))
        painter.drawRoundedRect(QRectF(r), 8, 8)
        self._paint_chevron(painter, option, theme, option.rect.left() + 22, mid)

        files = index.model().rowCount(index)
        count_text = f"{files} file" + ("" if files == 1 else "s")
        small = QFont(option.font)
        small.setPixelSize(11)
        count_w = QFontMetrics(small).horizontalAdvance(count_text)
        painter.setFont(small)
        painter.setPen(QColor(theme.muted))
        painter.drawText(
            r.adjusted(0, 0, -12, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            count_text,
        )

        font = QFont(option.font)
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.DemiBold)
        left = option.rect.left() + 38
        available = r.right() - 24 - count_w - left
        painter.setFont(font)
        painter.setPen(QColor(theme.text))
        painter.drawText(
            QRect(left, r.top(), available, r.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            QFontMetrics(font).elidedText(
                short_path(index.data(Qt.ItemDataRole.DisplayRole) or ""),
                Qt.TextElideMode.ElideLeft, available,
            ),
        )

    def _paint_file(self, painter, option, index, theme):
        # Content sits in the lower part of the row; the top is breathing room.
        r = option.rect.adjusted(0, 12, 0, 0)
        mid = r.center().y()
        self._paint_chevron(painter, option, theme, r.left() + 22, mid)

        # "PDF" badge
        badge = QRectF(r.left() + 38, mid - 9, 30, 18)
        painter.setBrush(QColor(theme.danger_soft))
        painter.drawRoundedRect(badge, 5, 5)
        badge_font = QFont(option.font)
        badge_font.setPixelSize(9)
        badge_font.setWeight(QFont.Weight.Bold)
        painter.setFont(badge_font)
        painter.setPen(QColor(theme.danger))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, "PDF")

        # Match-count pill (right)
        count = index.data(ROLE_COUNT) or 0
        count_text = f"{count} match" + ("" if count == 1 else "es")
        pill_font = QFont(option.font)
        pill_font.setPixelSize(11)
        pill_font.setWeight(QFont.Weight.DemiBold)
        pill_w = QFontMetrics(pill_font).horizontalAdvance(count_text) + 18
        pill = QRectF(r.right() - 16 - pill_w, mid - 10, pill_w, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.accent_soft))
        painter.drawRoundedRect(pill, 10, 10)
        painter.setFont(pill_font)
        painter.setPen(QColor(theme.accent))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, count_text)

        # File name, then its folder in muted text
        path = index.data(ROLE_FILE_PATH) or ""
        text_left = r.left() + 78
        available = int(pill.left()) - 12 - text_left
        name_font = QFont(option.font)
        name_font.setPixelSize(14)
        name_font.setWeight(QFont.Weight.DemiBold)
        name_fm = QFontMetrics(name_font)
        name = name_fm.elidedText(
            os.path.basename(path), Qt.TextElideMode.ElideMiddle, available
        )
        painter.setFont(name_font)
        painter.setPen(QColor(theme.text))
        painter.drawText(
            QRect(text_left, r.top(), available, r.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name,
        )
        name_w = name_fm.horizontalAdvance(name) + 10
        if self.show_file_folder and available - name_w > 60:
            dir_font = QFont(option.font)
            dir_font.setPixelSize(12)
            folder = QFontMetrics(dir_font).elidedText(
                short_path(os.path.dirname(path)),
                Qt.TextElideMode.ElideLeft, available - name_w,
            )
            painter.setFont(dir_font)
            painter.setPen(QColor(theme.faint))
            painter.drawText(
                QRect(text_left + name_w, r.top(), available - name_w, r.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                folder,
            )

    def _paint_match(self, painter, option, index, theme):
        r = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        if selected or hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.accent_soft if selected else theme.hover))
            painter.drawRoundedRect(QRectF(r.adjusted(34, 2, -12, -2)), 9, 9)

        match: MatchContext = index.data(ROLE_MATCH)

        # Page chip
        chip_font = QFont(option.font)
        chip_font.setPixelSize(11)
        chip_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(chip_font)
        painter.setPen(QColor(theme.accent if selected else theme.muted))
        painter.drawText(
            QRect(r.left() + 44, r.top(), self.SNIPPET_X - 56, r.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f"p. {match.page_number}",
        )

        # Snippet: two lines, search term highlighted
        doc = QTextDocument()
        font = QFont(option.font)
        font.setPixelSize(13)
        doc.setDefaultFont(font)
        doc.setDocumentMargin(0)
        term = " ".join(match.match_text.split())
        doc.setHtml(
            f'<span style="color:{theme.muted}">'
            f'{html.escape(match.context_before)} '
            f'<span style="background-color:{theme.mark_bg}; '
            f'color:{theme.mark_text}; font-weight:600">'
            f'{html.escape(term)}</span>'
            f' {html.escape(match.context_after)}</span>'
        )
        width = r.width() - self.SNIPPET_X - 28
        doc.setTextWidth(width)
        line_h = QFontMetrics(font).lineSpacing()
        text_h = min(doc.size().height(), 2 * line_h + 1)
        painter.translate(r.left() + self.SNIPPET_X,
                          r.top() + (r.height() - text_h) / 2)
        doc.drawContents(painter, QRectF(0, 0, width, text_h))


class ResultsPanel(QWidget):
    """Right panel displaying search results grouped by file."""

    open_pdf_requested = pyqtSignal(str, int)   # file_path, page_number
    reveal_requested = pyqtSignal(str)          # file_path

    PAGE_WELCOME, PAGE_RESULTS, PAGE_MESSAGE = range(3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultsPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._match_total = 0
        self._file_total = 0
        self._results: list[FileResult] = []
        self._folder_items: dict[str, QTreeWidgetItem] = {}
        self._sort = "found"
        self._group = "file"
        self.preview = PdfPreviewPopup(self)
        self._hover_item: QTreeWidgetItem | None = None
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(HOVER_PREVIEW_DELAY_MS)
        self._hover_timer.timeout.connect(self._show_hover_preview)
        self._setup_ui()
        QApplication.instance().applicationStateChanged.connect(
            lambda _state: self.hide_preview()
        )

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header: summary on the left, filter on the right
        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 12, 16, 4)
        header_layout.setSpacing(12)

        self.summary_label = QLabel("")
        self.summary_label.setObjectName("summaryLabel")
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        header_layout.addWidget(self.summary_label, 1)

        self.sort_button, self._sort_actions = self._menu_button(
            "Sort", SORT_OPTIONS, self.set_sort
        )
        header_layout.addWidget(self.sort_button)
        self.group_button, self._group_actions = self._menu_button(
            "Group", GROUP_OPTIONS, self.set_group
        )
        header_layout.addWidget(self.group_button)
        self._update_menu_buttons()

        self.filter_input = QLineEdit()
        self.filter_input.setObjectName("resultsFilter")
        self.filter_input.setPlaceholderText("Filter these results…")
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.setFixedWidth(190)
        self.filter_input.textChanged.connect(self._apply_filter)
        header_layout.addWidget(self.filter_input)
        layout.addWidget(self.header)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        # Page 0: welcome
        self.stack.addWidget(self._message_page(
            "Search inside your PDFs",
            "Pick folders or PDFs on the left — or drop them anywhere in this "
            "window —<br>then type what you're looking for and press Return."
            "<br><br>Hover a result to peek at the page, click to read it "
            "here,<br>or double-click to open it in Preview.",
        )[0])

        # Page 1: results tree
        self.tree = QTreeWidget()
        self.tree.setObjectName("resultsTree")
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setIndentation(0)
        self.tree.setRootIsDecorated(False)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setUniformRowHeights(False)
        self.tree.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.tree.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.tree.setMouseTracking(True)
        self.tree.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.tree.setItemDelegate(ResultDelegate(self.tree))
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_activated)
        self.tree.itemEntered.connect(self._on_item_entered)
        self.tree.currentItemChanged.connect(self._on_current_changed)
        self.tree.verticalScrollBar().valueChanged.connect(
            lambda _v: self.hide_preview()
        )
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.viewport().installEventFilter(self)
        self.tree.installEventFilter(self)

        # Page viewer (right of the list; hidden until a match is clicked)
        self.viewer = PageViewer()
        self.viewer.setVisible(False)
        self.viewer.next_match_requested.connect(lambda: self.step_match(1))
        self.viewer.prev_match_requested.connect(lambda: self.step_match(-1))
        self.viewer.open_external_requested.connect(self.open_pdf_requested)
        self.viewer.close_requested.connect(self.close_viewer)

        self.results_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.results_splitter.addWidget(self.tree)
        self.results_splitter.addWidget(self.viewer)
        self.results_splitter.setChildrenCollapsible(False)
        self.results_splitter.setStretchFactor(0, 1)
        self.results_splitter.setStretchFactor(1, 1)
        self.stack.addWidget(self.results_splitter)

        # Page 2: status message (searching / no matches)
        page, self.message_title, self.message_body = self._message_page("", "")
        self.stack.addWidget(page)

        self.header.setVisible(False)

    def _menu_button(self, prefix: str, options, on_pick):
        """A pill button that pops up a menu of exclusive choices."""
        button = QPushButton()
        button.setObjectName("menuButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setProperty("prefix", prefix)
        menu = QMenu(button)
        group = QActionGroup(menu)
        actions = {}
        for key, label in options:
            action = QAction(label, menu)
            action.setCheckable(True)
            action.triggered.connect(lambda _checked, k=key: on_pick(k))
            group.addAction(action)
            menu.addAction(action)
            actions[key] = action
        button.clicked.connect(
            lambda: menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        )
        return button, actions

    def _update_menu_buttons(self):
        for button, actions, current in (
            (self.sort_button, self._sort_actions, self._sort),
            (self.group_button, self._group_actions, self._group),
        ):
            actions[current].setChecked(True)
            button.setText(
                f"{button.property('prefix')}: {actions[current].text()}  ▾"
            )

    # --- sorting and grouping ---

    def get_sort(self) -> str:
        return self._sort

    def get_group(self) -> str:
        return self._group

    def set_sort(self, sort: str):
        if sort in self._sort_actions and sort != self._sort:
            self._sort = sort
            self._update_menu_buttons()
            self._rebuild()

    def set_group(self, group: str):
        if group in self._group_actions and group != self._group:
            self._group = group
            self._update_menu_buttons()
            self._rebuild()

    def _ordered_results(self) -> list[FileResult]:
        results = list(self._results)
        if self._sort == "name":
            results.sort(key=lambda r: r.file_name.lower())
        elif self._sort == "matches":
            results.sort(key=lambda r: -len(r.matches))
        elif self._sort == "modified":
            def mtime(r: FileResult) -> float:
                try:
                    return os.path.getmtime(r.file_path)
                except OSError:
                    return 0.0
            results.sort(key=mtime, reverse=True)
        if self._group == "folder":
            # Stable sort: folders A–Z, files keep the chosen order inside.
            results.sort(key=lambda r: os.path.dirname(r.file_path).lower())
        return results

    def _rebuild(self):
        """Re-create the tree from stored results in the current order."""
        current = self.tree.currentItem()
        selected = current.data(0, ROLE_MATCH) if current else None
        self.hide_preview()
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        self._folder_items.clear()
        for result in self._ordered_results():
            self._add_file_item(result)
        self.tree.setUpdatesEnabled(True)
        self._apply_filter(self.filter_input.text())
        if selected is not None:
            for item in self._all_match_items():
                if item.data(0, ROLE_MATCH) is selected:
                    self.tree.setCurrentItem(item)
                    self.tree.scrollToItem(item)
                    break

    @staticmethod
    def _message_page(title: str, body: str):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 80)
        layout.addStretch()
        title_label = QLabel(title)
        title_label.setObjectName("emptyTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacing(8)
        body_label = QLabel(body)
        body_label.setObjectName("emptyBody")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setTextFormat(Qt.TextFormat.RichText)
        body_label.setWordWrap(True)
        layout.addWidget(body_label)
        layout.addStretch()
        return page, title_label, body_label

    # --- search lifecycle ---

    def begin_search(self, query: str):
        """Reset for a new search and show a 'searching' message."""
        self._reset()
        self.message_title.setText("Searching…")
        self.message_body.setText(
            f"Looking for “{html.escape(query)}”. "
            "Results appear here as they're found."
        )
        self.stack.setCurrentIndex(self.PAGE_MESSAGE)

    def add_file_result(self, result: FileResult):
        """Add results for a file incrementally."""
        if not result.matches and not result.error:
            return
        self._results.append(result)
        self._add_file_item(result)
        self._file_total += 1
        self._match_total += len(result.matches)
        self._update_running_summary()
        self.header.setVisible(True)
        self.stack.setCurrentIndex(self.PAGE_RESULTS)

    def _parent_for(self, result: FileResult):
        """The tree itself, or this file's folder header when grouping."""
        ResultDelegate.show_file_folder = self._group != "folder"
        if self._group != "folder":
            return self.tree
        folder = os.path.dirname(result.file_path)
        item = self._folder_items.get(folder)
        if item is None:
            item = QTreeWidgetItem(self.tree)
            item.setData(0, ROLE_KIND, "folder")
            item.setText(0, folder)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item.setExpanded(True)
            self._folder_items[folder] = item
        return item

    def _add_file_item(self, result: FileResult):
        file_item = QTreeWidgetItem(self._parent_for(result))
        file_item.setData(0, ROLE_KIND, "file")
        file_item.setData(0, ROLE_FILE_PATH, result.file_path)
        file_item.setData(0, ROLE_COUNT, len(result.matches))
        file_item.setText(0, result.file_name)
        file_item.setToolTip(0, short_path(result.file_path))
        # File headers toggle open/closed; they aren't selectable rows.
        file_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

        if result.error:
            error_item = QTreeWidgetItem(file_item)
            error_item.setData(0, ROLE_KIND, "error")
            error_item.setData(0, ROLE_FILE_PATH, result.file_path)
            error_item.setText(0, f"Couldn't read this file: {result.error}")
        else:
            for match in result.matches:
                match_item = QTreeWidgetItem(file_item)
                match_item.setData(0, ROLE_KIND, "match")
                match_item.setData(0, ROLE_FILE_PATH, result.file_path)
                match_item.setData(0, ROLE_MATCH, match)
                # Plain text is used by the filter box.
                match_item.setText(
                    0,
                    f"{match.context_before} {match.match_text} "
                    f"{match.context_after}",
                )

        file_item.setExpanded(True)

    def finish_search(self, results: SearchResults, query: str):
        """Show the final summary, or a friendly message if nothing matched."""
        files = results.files_searched
        searched = f"{files} PDF{'' if files == 1 else 's'} searched"
        if self.tree.topLevelItemCount() == 0:
            self.header.setVisible(False)
            if files == 0:
                self.message_title.setText("No PDFs found")
                self.message_body.setText(
                    "There are no PDF files in the places you picked. "
                    "Try adding another folder, or turn on “Include subfolders”."
                )
            else:
                self.message_title.setText("No matches")
                self.message_body.setText(
                    f"Nothing found for “{html.escape(query)}” "
                    f"({searched}).<br>Check the spelling or try fewer words. "
                    "Scanned PDFs without a text layer can't be searched yet."
                )
            self.stack.setCurrentIndex(self.PAGE_MESSAGE)
            return
        self.summary_label.setText(
            f"{self._summary_counts()}"
            f" &nbsp;·&nbsp; {searched} in {results.elapsed_seconds:.1f}s"
        )
        # Results stream in as found; apply the chosen order once complete.
        if self._sort != "found" or self._group == "folder":
            self._rebuild()

    def clear_results(self):
        """Back to the welcome screen."""
        self._reset()
        self.stack.setCurrentIndex(self.PAGE_WELCOME)

    def _reset(self):
        self.hide_preview()
        self.close_viewer()
        self.viewer.clear()
        self.tree.clear()
        self._results = []
        self._folder_items.clear()
        self._match_total = 0
        self._file_total = 0
        self.summary_label.setText("")
        self.filter_input.clear()
        self.header.setVisible(False)

    def _summary_counts(self) -> str:
        theme = current_theme()
        m, f = self._match_total, self._file_total
        return (
            f'<span style="color:{theme.text}; font-weight:600">'
            f'{m} match{"" if m == 1 else "es"}</span>'
            f' in {f} file{"" if f == 1 else "s"}'
        )

    def _update_running_summary(self):
        self.summary_label.setText(self._summary_counts())

    # --- PDF preview popup ---

    def hide_preview(self):
        self._hover_timer.stop()
        self._hover_item = None
        self.preview.hide()

    def _show_preview_for(self, item: QTreeWidgetItem):
        match = item.data(0, ROLE_MATCH)
        # The hover peek is redundant while the page viewer is open.
        if match is None or not self.isVisible() or self.viewer.isVisible():
            self.preview.hide()
            return
        row = self.tree.visualItemRect(item)
        viewport = self.tree.viewport()
        anchor = QRect(
            viewport.mapToGlobal(row.topLeft()), row.size()
        ).adjusted(ResultDelegate.SNIPPET_X, 0, 0, 0)
        self.preview.show_match(item.data(0, ROLE_FILE_PATH), match, anchor)

    def _show_hover_preview(self):
        if self._hover_item is not None:
            self._show_preview_for(self._hover_item)

    def _on_item_entered(self, item: QTreeWidgetItem, _column: int):
        if item.data(0, ROLE_KIND) != "match":
            self.hide_preview()
            return
        if item is self._hover_item:
            return
        self._hover_item = item
        # Already showing a preview? Follow the mouse quickly.
        self._hover_timer.start(80 if self.preview.isVisible()
                                else HOVER_PREVIEW_DELAY_MS)

    def _on_current_changed(self, current, _previous):
        # Keyboard navigation: the viewer (or hover peek) follows the row.
        if current is None or not self.tree.hasFocus() \
                or current.data(0, ROLE_KIND) != "match":
            return
        if self.viewer.isVisible():
            self._open_in_viewer(current)
        else:
            self._hover_item = current
            self._show_preview_for(current)

    # --- page viewer ---

    def _all_match_items(self) -> list[QTreeWidgetItem]:
        """Match rows in display order, skipping ones hidden by the filter."""
        items = []
        it = QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            if item.data(0, ROLE_KIND) == "match" and not item.isHidden():
                items.append(item)
            it += 1
        return items

    def _open_in_viewer(self, item: QTreeWidgetItem):
        match = item.data(0, ROLE_MATCH)
        if match is None:
            return
        self.hide_preview()
        items = self._all_match_items()
        index = next((i for i, it in enumerate(items) if it is item), 0) + 1
        if not self.viewer.isVisible():
            self.viewer.setVisible(True)
            total = max(self.results_splitter.width(), 700)
            self.results_splitter.setSizes([int(total * 0.42), int(total * 0.58)])
        self.viewer.show_match(
            item.data(0, ROLE_FILE_PATH), match, index, len(items)
        )

    def close_viewer(self):
        self.viewer.setVisible(False)

    def step_match(self, step: int):
        """Select the next (+1) or previous (-1) match and show it."""
        items = self._all_match_items()
        if not items:
            return
        current = self.tree.currentItem()
        index = next((i for i, it in enumerate(items) if it is current), None)
        index = 0 if index is None else (index + step) % len(items)
        item = items[index]
        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item)
        self._open_in_viewer(item)

    def eventFilter(self, obj, event):
        if obj is self.tree.viewport() and event.type() == QEvent.Type.Leave:
            self.hide_preview()
        elif obj is self.tree and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = self.tree.currentItem()
                if item is not None:
                    self._on_item_activated(item, 0)
                    return True
            elif event.key() == Qt.Key.Key_Escape:
                if self.preview.isVisible():
                    self.hide_preview()
                else:
                    self.close_viewer()
                return True
        elif obj is self.tree and event.type() == QEvent.Type.FocusOut:
            self.hide_preview()
        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        self.hide_preview()
        super().hideEvent(event)

    # --- interaction ---

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int):
        kind = item.data(0, ROLE_KIND)
        if kind in ("file", "folder"):
            item.setExpanded(not item.isExpanded())
            self.hide_preview()
        elif kind == "match":
            self._open_in_viewer(item)

    def _on_item_activated(self, item: QTreeWidgetItem, _column: int):
        """Open the PDF at the matched page (double-click or Return)."""
        file_path = item.data(0, ROLE_FILE_PATH)
        if not file_path:
            return
        match = item.data(0, ROLE_MATCH)
        if item.data(0, ROLE_KIND) == "file":
            # The single click already toggled it; undo that for a double-click.
            item.setExpanded(True)
        self.hide_preview()
        self.open_pdf_requested.emit(file_path, match.page_number if match else 1)

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
        file_path = item.data(0, ROLE_FILE_PATH)
        if not file_path:
            return
        self.hide_preview()
        match: MatchContext | None = item.data(0, ROLE_MATCH)

        menu = QMenu(self)

        open_action = QAction(
            f"Open Page {match.page_number} in Preview" if match
            else "Open in Preview", self,
        )
        open_action.triggered.connect(
            lambda: self.open_pdf_requested.emit(
                file_path, match.page_number if match else 1
            )
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

        if match:
            copy_snippet_action = QAction("Copy Surrounding Text", self)
            copy_snippet_action.triggered.connect(
                lambda: QApplication.clipboard().setText(match.extended_context)
            )
            menu.addAction(copy_snippet_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _apply_filter(self, text: str):
        """Filter displayed results by text (matches snippets or file names)."""
        self.hide_preview()
        text_lower = text.lower()

        def visit(item: QTreeWidgetItem, show_all: bool) -> bool:
            kind = item.data(0, ROLE_KIND)
            if kind in ("match", "error"):
                visible = show_all or text_lower in item.text(0).lower()
            else:
                if kind == "file" and text_lower in item.text(0).lower():
                    show_all = True
                visible = False
                for i in range(item.childCount()):
                    visible = visit(item.child(i), show_all) or visible
            item.setHidden(not visible)
            return visible

        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i), not text)
