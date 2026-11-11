"""Theme for PDF Search Tool: light and dark palettes that follow the system.

Colors live in one place (``Theme``) so the stylesheet and the custom-painted
widgets (results list, PDF preview popup) always agree.
"""

from dataclasses import dataclass
from string import Template

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication


@dataclass(frozen=True)
class Theme:
    window: str         # main background
    surface: str        # raised areas: top bar, inputs, popups
    sidebar: str
    border: str
    text: str
    muted: str          # secondary text
    faint: str          # placeholder / tertiary text
    hover: str          # row hover background
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str    # selected row / checked chip background
    on_accent: str
    danger: str
    danger_soft: str
    mark_bg: str        # highlighted search term in snippets
    mark_text: str


LIGHT = Theme(
    window="#f6f6f8",
    surface="#ffffff",
    sidebar="#eeeef2",
    border="#dedee5",
    text="#1d1d1f",
    muted="#6b6b76",
    faint="#9a9aa5",
    hover="#e9e9ef",
    accent="#5b5bd6",
    accent_hover="#4e4ec7",
    accent_pressed="#4343b3",
    accent_soft="#e6e6fb",
    on_accent="#ffffff",
    danger="#d93f45",
    danger_soft="#fde8e8",
    mark_bg="#ffe066",
    mark_text="#1d1d1f",
)

DARK = Theme(
    window="#19191c",
    surface="#232327",
    sidebar="#1e1e22",
    border="#34343b",
    text="#ededf0",
    muted="#a0a0ab",
    faint="#6f6f7a",
    hover="#2a2a30",
    accent="#8483f2",
    accent_hover="#9594f5",
    accent_pressed="#7170e0",
    accent_soft="#2e2e52",
    on_accent="#ffffff",
    danger="#f2686c",
    danger_soft="#472326",
    mark_bg="#f5d04e",
    mark_text="#1d1d1f",
)


def current_theme() -> Theme:
    """Return the palette matching the system's light/dark appearance."""
    scheme = QGuiApplication.styleHints().colorScheme()
    return DARK if scheme == Qt.ColorScheme.Dark else LIGHT


_QSS = Template("""
QMainWindow, QDialog, QMessageBox {
    background-color: $window;
}

QWidget {
    color: $text;
    font-size: 13px;
}

QLabel {
    background-color: transparent;
}

QLabel#sectionLabel {
    font-size: 11px;
    font-weight: 600;
    color: $muted;
    padding-top: 6px;
}

QLabel#mutedLabel {
    color: $muted;
    font-size: 12px;
}

QToolTip {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
    padding: 4px 6px;
}

/* ===== Top search bar ===== */
QWidget#searchBar {
    background-color: $surface;
    border-bottom: 1px solid $border;
}

QLineEdit {
    padding: 6px 10px;
    border: 1px solid $border;
    border-radius: 8px;
    background-color: $surface;
    color: $text;
    selection-background-color: $accent;
    selection-color: $on_accent;
}

QLineEdit:focus {
    border: 1px solid $accent;
}

QLineEdit#queryInput {
    font-size: 16px;
    padding: 9px 12px;
    border-radius: 12px;
    background-color: $window;
}

QLineEdit#queryInput:focus {
    background-color: $surface;
    border: 2px solid $accent;
    padding: 8px 11px;
}

QLineEdit#resultsFilter {
    font-size: 12px;
    padding: 5px 12px;
    border-radius: 14px;
}

/* Segmented control (search mode) */
QWidget#segmented {
    background-color: $hover;
    border-radius: 9px;
}

QPushButton#segment {
    border: none;
    border-radius: 7px;
    padding: 4px 14px;
    min-height: 20px;
    background-color: transparent;
    color: $muted;
}

QPushButton#segment:hover {
    color: $text;
}

QPushButton#segment:checked {
    background-color: $surface;
    color: $text;
    font-weight: 600;
}

/* Toggle chip (match case) */
QPushButton#chip {
    border: 1px solid $border;
    border-radius: 13px;
    padding: 3px 12px;
    min-height: 20px;
    background-color: transparent;
    color: $muted;
}

QPushButton#chip:hover {
    background-color: $hover;
}

QPushButton#chip:checked {
    background-color: $accent_soft;
    border-color: $accent;
    color: $accent;
    font-weight: 600;
}

/* ===== Buttons ===== */
QPushButton {
    padding: 6px 14px;
    border: 1px solid $border;
    border-radius: 8px;
    background-color: $surface;
    color: $text;
    min-height: 20px;
}

QPushButton:hover {
    background-color: $hover;
}

QPushButton:pressed {
    background-color: $border;
}

QPushButton#searchButton {
    background-color: $accent;
    color: $on_accent;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 14px;
    padding: 9px 22px;
}

QPushButton#searchButton:hover {
    background-color: $accent_hover;
}

QPushButton#searchButton:pressed {
    background-color: $accent_pressed;
}

QPushButton#searchButton:disabled {
    background-color: $hover;
    color: $faint;
}

QPushButton#cancelButton {
    background-color: $danger_soft;
    color: $danger;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 14px;
    padding: 9px 22px;
}

QPushButton#dangerButton {
    color: $danger;
}

QPushButton#addSourceButton {
    font-size: 12px;
    font-weight: 600;
    padding: 4px 10px;
    color: $accent;
    background-color: transparent;
}

QPushButton#addSourceButton:hover {
    background-color: $accent_soft;
    border-color: $accent;
}

QPushButton#removeSourceButton {
    font-size: 12px;
    padding: 4px 10px;
    color: $muted;
    background-color: transparent;
    border-color: transparent;
}

QPushButton#removeSourceButton:hover {
    color: $danger;
    background-color: $danger_soft;
}

QPushButton#removeSourceButton:disabled {
    color: $faint;
}

QCheckBox {
    background-color: transparent;
    spacing: 6px;
}

/* ===== Sidebar ===== */
QWidget#sidebar {
    background-color: $sidebar;
    border-right: 1px solid $border;
}

QListWidget {
    font-size: 13px;
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 5px 6px;
    border-radius: 7px;
    color: $text;
}

QListWidget::item:hover {
    background-color: $hover;
}

QListWidget::item:selected {
    background-color: $accent_soft;
    color: $text;
}

QDialog QListWidget {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 4px;
}

/* ===== Results ===== */
QWidget#resultsPanel {
    background-color: $window;
}

QTreeWidget#resultsTree {
    background-color: $window;
    border: none;
    outline: none;
    selection-background-color: transparent;
}

QTreeWidget#resultsTree::item,
QTreeWidget#resultsTree::item:selected,
QTreeWidget#resultsTree::item:hover {
    background-color: transparent;
    border: none;
}

QTreeWidget#resultsTree::branch {
    background-color: transparent;
    image: none;
    border-image: none;
}

QLabel#summaryLabel {
    font-size: 13px;
    color: $muted;
}

QLabel#emptyTitle {
    font-size: 20px;
    font-weight: 600;
    color: $text;
}

QLabel#emptyBody {
    font-size: 13px;
    color: $muted;
}

/* Compact buttons: sort/group menus and viewer toolbar */
QPushButton#menuButton {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 14px;
    color: $muted;
    background-color: transparent;
}

QPushButton#menuButton:hover {
    color: $text;
    background-color: $hover;
}

QPushButton#toolButton {
    font-size: 12px;
    padding: 3px 9px;
    border: 1px solid transparent;
    border-radius: 7px;
    background-color: transparent;
    color: $text;
}

QPushButton#toolButton:hover {
    background-color: $hover;
}

QPushButton#toolButton:pressed {
    background-color: $border;
}

QPushButton#toolButton:disabled {
    color: $faint;
}

/* ===== Page viewer ===== */
QWidget#pageViewer {
    background-color: $window;
    border-left: 1px solid $border;
}

QLabel#viewerTitle {
    font-size: 13px;
    font-weight: 600;
}

QScrollArea#pageScroll {
    border: none;
    border-top: 1px solid $border;
    background-color: $hover;
}

QWidget#pageCanvas {
    background-color: $hover;
}

QLabel#pageImage {
    border: 1px solid $border;
    background-color: #ffffff;
    color: #55555f;
}

/* ===== Progress + status ===== */
QProgressBar#searchProgress {
    border: none;
    background-color: transparent;
    min-height: 3px;
    max-height: 3px;
}

QProgressBar#searchProgress::chunk {
    background-color: $accent;
}

QStatusBar {
    font-size: 12px;
    color: $muted;
    background-color: $window;
    border-top: 1px solid $border;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: $muted;
    font-size: 12px;
    padding-left: 6px;
}

QSplitter::handle {
    background-color: $border;
    width: 1px;
}

/* ===== Menus ===== */
QMenu {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 22px;
    border-radius: 5px;
}

QMenu::item:selected {
    background-color: $accent;
    color: $on_accent;
}

QMenu::separator {
    height: 1px;
    background-color: $border;
    margin: 4px 8px;
}

/* ===== Scrollbars ===== */
QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    border: none;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: $border;
    border-radius: 3px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: $faint;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 10px;
    border: none;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: $border;
    border-radius: 3px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background-color: $faint;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}

QScrollBar::add-page, QScrollBar::sub-page {
    background-color: transparent;
}
""")


def build_stylesheet(theme: Theme) -> str:
    return _QSS.substitute(theme.__dict__)
