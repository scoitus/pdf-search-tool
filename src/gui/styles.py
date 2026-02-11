"""Dark mode QSS stylesheet for PDF Search Tool."""

MACOS_STYLESHEET = """
/* ===== Global dark backgrounds ===== */
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

/* Search panel */
QWidget#searchPanel {
    background-color: #252525;
    border-right: 1px solid #3a3a3a;
}

QLabel {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 13px;
    color: #e0e0e0;
    background-color: transparent;
}

QLabel#sectionLabel {
    font-weight: 600;
    font-size: 12px;
    color: #8e8e93;
    text-transform: uppercase;
    padding-top: 8px;
    background-color: transparent;
}

/* ===== Text inputs ===== */
QLineEdit {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 14px;
    padding: 6px 10px;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    background-color: #2d2d2d;
    color: #e0e0e0;
    selection-background-color: #0a84ff;
    selection-color: white;
}

QLineEdit:focus {
    border-color: #0a84ff;
    border-width: 2px;
    padding: 5px 9px;
}

QLineEdit::placeholder {
    color: #6e6e73;
}

/* ===== Radio buttons & checkboxes ===== */
QRadioButton, QCheckBox {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 13px;
    color: #e0e0e0;
    spacing: 6px;
    background-color: transparent;
}

QRadioButton::indicator, QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

/* ===== Buttons ===== */
QPushButton {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 13px;
    padding: 6px 16px;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    background-color: #3a3a3a;
    color: #e0e0e0;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #484848;
}

QPushButton:pressed {
    background-color: #555555;
}

QPushButton#searchButton {
    background-color: #0a84ff;
    color: white;
    border: none;
    font-weight: 600;
    font-size: 14px;
    padding: 8px 20px;
    min-height: 28px;
}

QPushButton#searchButton:hover {
    background-color: #0070e0;
}

QPushButton#searchButton:pressed {
    background-color: #005bbf;
}

QPushButton#searchButton:disabled {
    background-color: #1a4a7a;
    color: #6e6e73;
}

QPushButton#cancelButton {
    background-color: #ff453a;
    color: white;
    border: none;
    font-weight: 500;
}

QPushButton#cancelButton:hover {
    background-color: #d63028;
}

QPushButton#addFolderButton {
    font-size: 18px;
    padding: 2px 8px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 14px;
    background-color: #3a3a3a;
    color: #0a84ff;
}

QPushButton#addFolderButton:hover {
    background-color: #484848;
}

QPushButton#removeFolderButton {
    font-size: 18px;
    padding: 2px 8px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 14px;
    background-color: #3a3a3a;
    color: #ff453a;
}

QPushButton#removeFolderButton:hover {
    background-color: #484848;
}

/* ===== Results tree ===== */
QTreeWidget {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 13px;
    background-color: #1e1e1e;
    alternate-background-color: #242424;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    outline: none;
    color: #e0e0e0;
}

QTreeWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #2a2a2a;
    color: #e0e0e0;
}

QTreeWidget::item:selected {
    background-color: #0a84ff;
    color: white;
}

QTreeWidget::item:hover:!selected {
    background-color: #2a3a4a;
}

QTreeWidget::branch {
    background-color: transparent;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    image: none;
    border-image: none;
}

QHeaderView {
    background-color: #252525;
}

QHeaderView::section {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: #8e8e93;
    background-color: #252525;
    border: none;
    border-bottom: 1px solid #3a3a3a;
    padding: 6px 8px;
}

/* ===== Folder list ===== */
QListWidget {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 12px;
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    color: #e0e0e0;
}

QListWidget::item {
    padding: 4px 6px;
    color: #e0e0e0;
}

QListWidget::item:selected {
    background-color: #0a84ff;
    color: white;
}

/* ===== Status bar ===== */
QStatusBar {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 12px;
    color: #8e8e93;
    background-color: #252525;
    border-top: 1px solid #3a3a3a;
}

QStatusBar QLabel {
    color: #8e8e93;
    background-color: transparent;
}

/* ===== Progress bar ===== */
QProgressBar {
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    text-align: center;
    font-size: 11px;
    max-height: 16px;
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #0a84ff;
    border-radius: 3px;
}

/* ===== Splitter handle ===== */
QSplitter::handle {
    background-color: #3a3a3a;
    width: 1px;
}

/* ===== Menu bar ===== */
QMenuBar {
    font-family: 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 13px;
    background-color: #252525;
    color: #e0e0e0;
}

QMenuBar::item {
    background-color: transparent;
    color: #e0e0e0;
}

QMenuBar::item:selected {
    background-color: #0a84ff;
    color: white;
}

QMenu {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0a84ff;
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #3a3a3a;
    margin: 4px 8px;
}

/* ===== Filter input in results panel ===== */
QLineEdit#resultsFilter {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 10px;
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    color: #e0e0e0;
}

QLineEdit#resultsFilter:focus {
    background-color: #333333;
    border: 2px solid #0a84ff;
    padding: 3px 7px;
}

/* ===== Scrollbars ===== */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 10px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #4a4a4a;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a5a5a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 10px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #4a4a4a;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5a5a5a;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===== Snippet text area ===== */
QTextEdit#snippetView {
    background-color: #2a2a2a;
    color: #d0d0d0;
    border: none;
    border-left: 3px solid #0a84ff;
    padding: 8px;
    font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
    font-size: 12px;
    selection-background-color: #0a84ff;
    selection-color: white;
}

/* ===== Message boxes / Dialogs ===== */
QDialog {
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QMessageBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
}
"""
