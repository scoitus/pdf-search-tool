"""Top search bar: query field, search mode, match-case toggle, Search button."""

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QWidget,
)

from gui.styles import current_theme

PLACEHOLDERS = {
    "plain": "Search inside your PDFs…",
    "regex": r"Regular expression, e.g.  invoice\s+\d{4}",
    "boolean": "e.g.  (contract AND renewal) NOT draft",
}

MODE_HINTS = {
    "plain": "Finds the exact words you type.",
    "regex": "Pattern matching for power users.",
    "boolean": "Combine words with AND, OR, NOT and parentheses.",
}


def _magnifier_icon(color: str) -> QIcon:
    """Draw a small magnifying-glass icon (no image assets needed)."""
    size = 32
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 3.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawEllipse(QRectF(5, 5, 16, 16))
    painter.drawLine(QPointF(19.5, 19.5), QPointF(27, 27))
    painter.end()
    return QIcon(pixmap)


class SearchBar(QWidget):
    """Header strip holding everything about *what* to search for."""

    search_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    query_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(10)

        # --- Row 1: query + action button ---
        top = QHBoxLayout()
        top.setSpacing(10)

        self.query_input = QLineEdit()
        self.query_input.setObjectName("queryInput")
        self.query_input.setClearButtonEnabled(True)
        self._icon_action = self.query_input.addAction(
            _magnifier_icon(current_theme().faint),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.query_input.returnPressed.connect(self.search_requested.emit)
        self.query_input.textChanged.connect(lambda _: self.query_changed.emit())
        top.addWidget(self.query_input, 1)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("searchButton")
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.clicked.connect(self.search_requested.emit)
        top.addWidget(self.search_btn)

        self.cancel_btn = QPushButton("Stop")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        self.cancel_btn.setVisible(False)
        top.addWidget(self.cancel_btn)

        layout.addLayout(top)

        # --- Row 2: mode + options ---
        options = QHBoxLayout()
        options.setSpacing(10)

        segmented = QWidget()
        segmented.setObjectName("segmented")
        segmented.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        seg_layout = QHBoxLayout(segmented)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(2)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self._mode_buttons: dict[str, QPushButton] = {}
        for mode, label in (("plain", "Text"), ("regex", "Regex"),
                            ("boolean", "Boolean")):
            btn = QPushButton(label)
            btn.setObjectName("segment")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(MODE_HINTS[mode])
            self.mode_group.addButton(btn)
            seg_layout.addWidget(btn)
            self._mode_buttons[mode] = btn
        self._mode_buttons["plain"].setChecked(True)
        self.mode_group.buttonToggled.connect(self._on_mode_changed)
        options.addWidget(segmented)

        self.case_sensitive_cb = QPushButton("Aa  Match case")
        self.case_sensitive_cb.setObjectName("chip")
        self.case_sensitive_cb.setCheckable(True)
        self.case_sensitive_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.case_sensitive_cb.setToolTip(
            "When on, “Invoice” and “invoice” are treated as different words"
        )
        options.addWidget(self.case_sensitive_cb)

        self.mode_hint = QLabel()
        self.mode_hint.setObjectName("mutedLabel")
        options.addWidget(self.mode_hint)
        options.addStretch()

        layout.addLayout(options)
        self._on_mode_changed()

    # --- internal ---

    def _on_mode_changed(self, *_):
        mode = self.get_mode()
        self.query_input.setPlaceholderText(PLACEHOLDERS[mode])
        self.mode_hint.setText(MODE_HINTS[mode])

    # --- public API ---

    def refresh_theme(self):
        self._icon_action.setIcon(_magnifier_icon(current_theme().faint))

    def get_query(self) -> str:
        return self.query_input.text().strip()

    def set_query(self, query: str):
        self.query_input.setText(query)

    def get_mode(self) -> str:
        for mode, btn in self._mode_buttons.items():
            if btn.isChecked():
                return mode
        return "plain"

    def set_mode(self, mode: str):
        self._mode_buttons.get(mode, self._mode_buttons["plain"]).setChecked(True)

    def is_case_sensitive(self) -> bool:
        return self.case_sensitive_cb.isChecked()

    def set_case_sensitive(self, value: bool):
        self.case_sensitive_cb.setChecked(value)

    def set_search_enabled(self, enabled: bool, tooltip: str = ""):
        self.search_btn.setEnabled(enabled)
        self.search_btn.setToolTip(tooltip)

    def set_searching(self, searching: bool):
        """Swap Search for Stop while a search is running."""
        self.search_btn.setVisible(not searching)
        self.cancel_btn.setVisible(searching)
        self.query_input.setEnabled(not searching)
