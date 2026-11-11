"""In-app page viewer: shows the full PDF page for the selected match."""

import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget,
)

from gui.pdf_preview import render_page
from models.search_result import MatchContext

ZOOM_STEP = 1.2
ZOOM_MIN = 0.5
ZOOM_MAX = 4.0
PAGE_MARGIN = 16


def _tool_button(text: str, tooltip: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName("toolButton")
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return btn


class PageViewer(QWidget):
    """Side pane rendering one PDF page, with match / page / zoom controls."""

    next_match_requested = pyqtSignal()
    prev_match_requested = pyqtSignal()
    open_external_requested = pyqtSignal(str, int)   # file_path, page_number
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pageViewer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(320)

        self._path: str | None = None
        self._match: MatchContext | None = None
        self._page = 1
        self._page_count = 1
        self._zoom = 1.0
        self._rendered_key = None
        self._scroll_to_match = False

        # Rendering is deferred so it uses the pane's final width, and so a
        # burst of resize events only re-renders once.
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._render)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 0, 0, 0)
        layout.setSpacing(0)

        # Row 1: file name + open/close
        top = QHBoxLayout()
        top.setContentsMargins(14, 10, 8, 2)
        top.setSpacing(4)
        self.title = QLabel("")
        self.title.setObjectName("viewerTitle")
        self.title.setSizePolicy(QSizePolicy.Policy.Ignored,
                                 QSizePolicy.Policy.Preferred)
        top.addWidget(self.title, 1)
        open_btn = _tool_button("Open in Preview", "Open this page in Preview")
        open_btn.clicked.connect(self._open_external)
        top.addWidget(open_btn)
        close_btn = _tool_button("✕", "Close the page viewer")
        close_btn.clicked.connect(self.close_requested.emit)
        top.addWidget(close_btn)
        layout.addLayout(top)

        # Row 2: match navigation | page navigation | zoom
        bar = QHBoxLayout()
        bar.setContentsMargins(8, 2, 8, 8)
        bar.setSpacing(2)

        prev_match = _tool_button("↑", "Previous match")
        prev_match.clicked.connect(self.prev_match_requested.emit)
        bar.addWidget(prev_match)
        next_match = _tool_button("↓", "Next match")
        next_match.clicked.connect(self.next_match_requested.emit)
        bar.addWidget(next_match)
        self.match_label = QLabel("")
        self.match_label.setObjectName("mutedLabel")
        bar.addWidget(self.match_label)

        bar.addStretch()

        self.prev_page_btn = _tool_button("‹", "Previous page")
        self.prev_page_btn.clicked.connect(lambda: self._go_to_page(self._page - 1))
        bar.addWidget(self.prev_page_btn)
        self.page_label = QLabel("")
        self.page_label.setObjectName("mutedLabel")
        bar.addWidget(self.page_label)
        self.next_page_btn = _tool_button("›", "Next page")
        self.next_page_btn.clicked.connect(lambda: self._go_to_page(self._page + 1))
        bar.addWidget(self.next_page_btn)

        bar.addStretch()

        zoom_out = _tool_button("−", "Zoom out")
        zoom_out.clicked.connect(lambda: self._set_zoom(self._zoom / ZOOM_STEP))
        bar.addWidget(zoom_out)
        fit = _tool_button("Fit", "Fit the page to the pane width")
        fit.clicked.connect(lambda: self._set_zoom(1.0))
        bar.addWidget(fit)
        zoom_in = _tool_button("+", "Zoom in")
        zoom_in.clicked.connect(lambda: self._set_zoom(self._zoom * ZOOM_STEP))
        bar.addWidget(zoom_in)
        layout.addLayout(bar)

        # Page canvas
        self.scroll = QScrollArea()
        self.scroll.setObjectName("pageScroll")
        self.scroll.setWidgetResizable(True)
        # Always-on so the fit-to-width size doesn't change when it appears.
        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        canvas = QWidget()
        canvas.setObjectName("pageCanvas")
        canvas.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN,
                                         PAGE_MARGIN, PAGE_MARGIN)
        self.page_image = QLabel()
        self.page_image.setObjectName("pageImage")
        self.page_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_layout.addWidget(
            self.page_image, 0,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        canvas_layout.addStretch()
        self.scroll.setWidget(canvas)
        layout.addWidget(self.scroll, 1)

    # --- public API ---

    def show_match(self, file_path: str, match: MatchContext,
                   index: int, total: int):
        """Display the page containing ``match`` and scroll it into view."""
        self._path = file_path
        self._match = match
        self._page = match.page_number
        self.match_label.setText(f"Match {index} of {total}")
        self._update_title()
        self._scroll_to_match = True
        self._render_timer.start(0)

    def clear(self):
        self._path = None
        self._match = None
        self._rendered_key = None
        self.page_image.clear()

    # --- internals ---

    def _update_title(self):
        name = os.path.basename(self._path) if self._path else ""
        self.title.setText(self.title.fontMetrics().elidedText(
            name, Qt.TextElideMode.ElideMiddle, max(60, self.title.width())
        ))
        self.title.setToolTip(self._path or "")

    def _go_to_page(self, page: int):
        if self._path and 1 <= page <= self._page_count:
            self._page = page
            self._scroll_to_match = self._on_match_page()
            self._render_timer.start(0)

    def _set_zoom(self, zoom: float):
        self._zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom))
        self._scroll_to_match = self._on_match_page()
        self._render_timer.start(0)

    def _on_match_page(self) -> bool:
        return self._match is not None and self._page == self._match.page_number

    def _open_external(self):
        if self._path:
            self.open_external_requested.emit(self._path, self._page)

    def _render(self):
        if not self._path or self._match is None or not self.isVisible():
            return
        fit_width = max(200, self.scroll.viewport().width() - 2 * PAGE_MARGIN - 2)
        key = (self._path, self._page, self._match.char_offset,
               self._match.match_text, fit_width, self._zoom)
        if key != self._rendered_key:
            offset = self._match.char_offset if self._on_match_page() else None
            self._render_result = render_page(
                self._path, self._page, self._match.match_text, offset,
                fit_width, self._zoom, self.devicePixelRatioF(),
            )
            self._rendered_key = key
            if self._render_result is None:
                self.page_image.setPixmap(QPixmap())
                self.page_image.setText(
                    "This page couldn't be displayed.\n"
                    "The file may have been moved or deleted."
                )
                self.page_image.setFixedSize(fit_width, 120)
            else:
                pixmap = QPixmap.fromImage(self._render_result.image)
                size = pixmap.deviceIndependentSize().toSize()
                self.page_image.setFixedSize(size.width() + 2, size.height() + 2)
                self.page_image.setPixmap(pixmap)
                self._page_count = self._render_result.page_count

        self.page_label.setText(f"Page {self._page} of {self._page_count}")
        self.prev_page_btn.setEnabled(self._page > 1)
        self.next_page_btn.setEnabled(self._page < self._page_count)

        if self._scroll_to_match:
            self._scroll_to_match = False
            # Wait for the layout to place the new page before scrolling.
            QTimer.singleShot(0, self._center_on_match)

    def _center_on_match(self):
        result = getattr(self, "_render_result", None)
        vbar, hbar = self.scroll.verticalScrollBar(), self.scroll.horizontalScrollBar()
        if result is None or result.target is None:
            vbar.setValue(0)
            return
        origin = self.page_image.pos()
        viewport = self.scroll.viewport()
        center = result.target.center()
        vbar.setValue(int(origin.y() + center.y() - viewport.height() / 2))
        hbar.setValue(int(origin.x() + center.x() - viewport.width() / 2))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_title()
        if self._path:
            self._render_timer.start(120)
