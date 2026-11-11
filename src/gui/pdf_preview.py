"""Floating preview showing the real PDF page region around a match.

``render_match_slice`` rasterizes a band of the page centered on the match
(with the hit highlighted); ``PdfPreviewPopup`` shows it in a small floating
card next to the result row.
"""

import os
from collections import OrderedDict
from dataclasses import dataclass

import fitz  # PyMuPDF
from PyQt6.QtCore import QPoint, QRect, QRectF, Qt
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QGuiApplication, QImage, QPainter,
    QPainterPath, QPen,
)
from PyQt6.QtWidgets import QWidget

from gui.styles import current_theme
from models.search_result import MatchContext
from search_engine import PDF_LOCK

SLICE_WIDTH = 600    # logical pixels
SLICE_HEIGHT = 260
MIN_SCALE = 0.9      # never shrink page text below this (crop sideways instead)
MAX_SCALE = 1.6

_HIT_COLOR = QColor("#ffd60a")        # the match this row points at
_OTHER_HIT_COLOR = QColor("#fff0a8")  # other occurrences on the same page


@dataclass
class MatchSlice:
    image: QImage
    page_count: int
    located: bool   # False if the match couldn't be pinpointed on the page


_cache: "OrderedDict[tuple, MatchSlice]" = OrderedDict()
_CACHE_SIZE = 48


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def _locate(page, match_text: str, char_offset: int | None):
    """Find where the matched text sits on the page.

    The search works on extracted text (character offsets); to get
    coordinates we ask MuPDF for every occurrence of the matched text and,
    if ``char_offset`` is given, pick the one at the same position in
    reading order. Returns (all_hits, target_or_None).
    """
    needle = _normalize(match_text)
    hits = page.search_for(needle) if needle else []
    target = None
    if hits and char_offset is not None:
        preceding = _normalize(page.get_text()[:char_offset])
        target = hits[min(preceding.count(needle), len(hits) - 1)]
    return hits, target


def _paint_hits(image: QImage, hits, target, origin, zoom: float, dpr: float):
    """Highlighter effect: multiply keeps the text itself crisp and dark."""
    painter = QPainter(image)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
    painter.setPen(Qt.PenStyle.NoPen)
    for hit in hits:
        painter.setBrush(_HIT_COLOR if hit == target else _OTHER_HIT_COLOR)
        painter.drawRoundedRect(
            QRectF((hit.x0 - origin.x) * zoom - 2 * dpr,
                   (hit.y0 - origin.y) * zoom - 1 * dpr,
                   hit.width * zoom + 4 * dpr,
                   hit.height * zoom + 2 * dpr),
            2 * dpr, 2 * dpr,
        )
    painter.end()


def _to_qimage(pix) -> QImage:
    return QImage(pix.samples, pix.width, pix.height, pix.stride,
                  QImage.Format.Format_RGB888).copy()


@dataclass
class PageRender:
    image: QImage
    page_count: int
    target: QRectF | None   # match position in logical pixels, if on this page


def render_page(file_path: str, page_number: int, match_text: str,
                char_offset: int | None, fit_width: float, zoom_factor: float,
                dpr: float) -> PageRender | None:
    """Render a whole page scaled to ``fit_width`` × ``zoom_factor``.

    Every occurrence of ``match_text`` is highlighted; pass ``char_offset``
    when the selected match is on this page to mark it as the target.
    """
    try:
        with PDF_LOCK:
            doc = fitz.open(file_path)
            try:
                page = doc[page_number - 1]
                hits, target = _locate(page, match_text, char_offset)
                scale = fit_width / page.rect.width * zoom_factor
                zoom = scale * dpr
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom),
                                      alpha=False)
                image = _to_qimage(pix)
                _paint_hits(image, hits, target, page.rect.tl, zoom, dpr)
                image.setDevicePixelRatio(dpr)
                target_rect = None
                if target is not None:
                    target_rect = QRectF(
                        (target.x0 - page.rect.x0) * scale,
                        (target.y0 - page.rect.y0) * scale,
                        target.width * scale, target.height * scale,
                    )
                return PageRender(image, len(doc), target_rect)
            finally:
                doc.close()
    except Exception:
        return None


def render_match_slice(file_path: str, match: MatchContext,
                       dpr: float) -> MatchSlice | None:
    """Render the area of the page around ``match``. Returns None on failure."""
    key = (file_path, match.page_number, match.char_offset, match.match_text, dpr)
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]

    try:
        with PDF_LOCK:
            result = _render(file_path, match, dpr)
    except Exception:
        return None

    _cache[key] = result
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)
    return result


def _render(file_path: str, match: MatchContext, dpr: float) -> MatchSlice:
    doc = fitz.open(file_path)
    try:
        page = doc[match.page_number - 1]
        page_rect = page.rect

        hits, target = _locate(page, match.match_text, match.char_offset)

        scale = max(MIN_SCALE, min(MAX_SCALE, SLICE_WIDTH / page_rect.width))
        clip_w = min(page_rect.width, SLICE_WIDTH / scale)
        clip_h = min(page_rect.height, SLICE_HEIGHT / scale)

        if target is not None:
            cx = (target.x0 + target.x1) / 2
            cy = (target.y0 + target.y1) / 2
        else:
            cx, cy = page_rect.width / 2, clip_h / 2   # top of the page

        x0 = max(page_rect.x0, min(cx - clip_w / 2, page_rect.x1 - clip_w))
        y0 = max(page_rect.y0, min(cy - clip_h / 2, page_rect.y1 - clip_h))
        clip = fitz.Rect(x0, y0, x0 + clip_w, y0 + clip_h)

        zoom = scale * dpr
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip,
                              alpha=False)
        image = _to_qimage(pix)
        _paint_hits(image, [h for h in hits if h.intersects(clip)], target,
                    clip.tl, zoom, dpr)

        image.setDevicePixelRatio(dpr)
        return MatchSlice(image=image, page_count=len(doc),
                          located=target is not None)
    finally:
        doc.close()


class PdfPreviewPopup(QWidget):
    """Frameless floating card showing a ``MatchSlice`` beside a result row."""

    PAD = 10
    HEADER_H = 30
    FOOTER_H = 26
    RADIUS = 12

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._slice: MatchSlice | None = None
        self._title = ""
        self._page_label = ""
        self._key = None

    def show_match(self, file_path: str, match: MatchContext, anchor: QRect):
        """Show the preview for ``match`` next to ``anchor`` (global coords)."""
        key = (file_path, match.page_number, match.char_offset)
        if key != self._key or self._slice is None:
            screen = QGuiApplication.screenAt(anchor.center())
            dpr = screen.devicePixelRatio() if screen else 2.0
            self._slice = render_match_slice(file_path, match, dpr)
            self._key = key
            if self._slice is None:
                self.hide()
                return
            self._title = os.path.basename(file_path)
            self._page_label = (
                f"Page {match.page_number} of {self._slice.page_count}"
            )

        size = self._slice.image.deviceIndependentSize()
        width = int(size.width()) + 2 * self.PAD
        height = int(size.height()) + self.HEADER_H + self.FOOTER_H
        self.resize(width, height)
        self.move(self._position_for(anchor, width, height))
        self.show()
        self.update()

    def _position_for(self, anchor: QRect, width: int, height: int) -> QPoint:
        """Below the row if it fits on screen, otherwise above it."""
        screen = QGuiApplication.screenAt(anchor.center())
        area = (screen or QGuiApplication.primaryScreen()).availableGeometry()
        gap = 6
        x = max(area.left() + 8, min(anchor.left(), area.right() - width - 8))
        y = anchor.bottom() + gap
        if y + height > area.bottom() - 8:
            y = anchor.top() - gap - height
        return QPoint(x, max(area.top() + 8, y))

    def paintEvent(self, event):
        if self._slice is None:
            return
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Card
        card = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(QColor(theme.border), 1))
        painter.setBrush(QColor(theme.surface))
        painter.drawRoundedRect(card, self.RADIUS, self.RADIUS)

        # Header: file name (left) and page (right)
        header = QRect(self.PAD + 2, 0, self.width() - 2 * self.PAD - 4,
                       self.HEADER_H)
        small = QFont(self.font())
        small.setPixelSize(11)
        painter.setFont(small)
        painter.setPen(QColor(theme.muted))
        painter.drawText(
            header,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            self._page_label,
        )
        page_w = QFontMetrics(small).horizontalAdvance(self._page_label)

        bold = QFont(self.font())
        bold.setPixelSize(12)
        bold.setWeight(QFont.Weight.DemiBold)
        painter.setFont(bold)
        painter.setPen(QColor(theme.text))
        title = QFontMetrics(bold).elidedText(
            self._title, Qt.TextElideMode.ElideMiddle,
            header.width() - page_w - 12,
        )
        painter.drawText(
            header,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title,
        )

        # Page slice, clipped to rounded corners
        size = self._slice.image.deviceIndependentSize()
        img_rect = QRectF(self.PAD, self.HEADER_H, size.width(), size.height())
        path = QPainterPath()
        path.addRoundedRect(img_rect, 6, 6)
        painter.save()
        painter.setClipPath(path)
        painter.drawImage(img_rect.topLeft(), self._slice.image)
        painter.restore()
        painter.setPen(QPen(QColor(theme.border), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Footer hint
        footer = QRect(self.PAD + 2, self.height() - self.FOOTER_H,
                       self.width() - 2 * self.PAD - 4, self.FOOTER_H)
        painter.setFont(small)
        painter.setPen(QColor(theme.faint))
        hint = "Double-click the result to open this page in Preview"
        if not self._slice.located:
            hint = "Couldn't pinpoint the match — showing the top of the page"
        painter.drawText(
            footer,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            hint,
        )
