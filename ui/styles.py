DARK_THEME_QSS = """
/* Global App Style */
QMainWindow, QDialog, QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #141721;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #2d3345;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #4f46e5;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #141721;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #2d3345;
    min-width: 25px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #4f46e5;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Main Tab Widget */
QTabWidget::pane {
    border: 1px solid #232736;
    background: #131620;
    border-radius: 10px;
    margin-top: -1px;
}
QTabBar::tab {
    background: #181b26;
    color: #94a3b8;
    padding: 10px 22px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #232736;
    border-bottom: none;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: #1f2433;
    color: #ffffff;
    border-top: 2px solid #6366f1;
}
QTabBar::tab:hover:!selected {
    background: #1c202d;
    color: #cbd5e1;
}

/* Sub Tab Widget (Inside Agent) */
QTabWidget#subTabWidget::pane {
    border: 1px solid #1e2230;
    background: #11141d;
    border-radius: 8px;
}
QTabWidget#subTabWidget QTabBar::tab {
    background: #161924;
    color: #94a3b8;
    padding: 8px 18px;
    font-size: 12px;
}
QTabWidget#subTabWidget QTabBar::tab:selected {
    background: #1c202d;
    color: #38bdf8;
    border-top: 2px solid #38bdf8;
}

/* Buttons */
QPushButton {
    background-color: #242938;
    color: #f1f5f9;
    border: 1px solid #333a4d;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #31374a;
    border-color: #4b5563;
}
QPushButton:pressed {
    background-color: #1e2330;
}
QPushButton:disabled {
    background-color: #161922;
    color: #475569;
    border-color: #1e222d;
}

/* Primary Button (Indigo / Blue) */
QPushButton#primaryBtn {
    background-color: #4f46e5;
    color: #ffffff;
    border: 1px solid #6366f1;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #4338ca;
    border-color: #818cf8;
}
QPushButton#primaryBtn:pressed {
    background-color: #3730a3;
}

/* Success Button (Emerald) */
QPushButton#successBtn {
    background-color: #059669;
    color: #ffffff;
    border: 1px solid #10b981;
    font-weight: 600;
}
QPushButton#successBtn:hover {
    background-color: #047857;
}

/* Danger Button (Red) */
QPushButton#dangerBtn {
    background-color: #991b1b;
    color: #ffffff;
    border: 1px solid #dc2626;
    padding: 6px 12px;
}
QPushButton#dangerBtn:hover {
    background-color: #b91c1c;
}

/* Warning / Amber Button */
QPushButton#warningBtn {
    background-color: #b45309;
    color: #ffffff;
    border: 1px solid #f59e0b;
    font-weight: 500;
}
QPushButton#warningBtn:hover {
    background-color: #92400e;
}

/* Secondary Button */
QPushButton#secondaryBtn {
    background-color: #1e2230;
    color: #cbd5e1;
    border: 1px solid #2d3345;
}
QPushButton#secondaryBtn:hover {
    background-color: #272d3f;
    color: #ffffff;
}

/* Input Fields & Text Edits */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background-color: #161924;
    color: #f1f5f9;
    border: 1px solid #2d3345;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #4f46e5;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #6366f1;
    background-color: #181d2a;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1a1e2b;
    color: #e2e8f0;
    border: 1px solid #333a4d;
    selection-background-color: #4f46e5;
}

/* Table Widget */
QTableWidget {
    background-color: #131620;
    border: 1px solid #222634;
    border-radius: 6px;
    gridline-color: #1e2230;
    color: #e2e8f0;
    font-size: 13px;
}
QTableWidget::item {
    padding: 4px 8px;
    font-size: 13px;
}
QTableWidget::item:selected {
    background-color: #242b3d;
    color: #ffffff;
}
QTableWidget QLineEdit, QTableView QLineEdit {
    background-color: #1a1e2d;
    color: #f8fafc;
    border: 1px solid #6366f1;
    border-radius: 4px;
    padding: 2px 6px;
    margin: 0px;
    font-size: 13px;
    font-family: inherit;
    min-height: 20px;
}
QHeaderView::section {
    background-color: #181c27;
    color: #94a3b8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #222634;
    font-weight: 600;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #232736;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: 600;
    color: #cbd5e1;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #0f1117;
}

/* Status Bar */
QStatusBar {
    background-color: #131620;
    border-top: 1px solid #1e2230;
    color: #94a3b8;
    font-size: 11px;
    padding: 4px 8px;
}

/* Labels */
QLabel {
    color: #cbd5e1;
}
QLabel#headerTitle {
    font-size: 18px;
    font-weight: 700;
    color: #f8fafc;
}
QLabel#cardTitle {
    font-size: 15px;
    font-weight: 600;
    color: #f8fafc;
}
QLabel#cardSubtitle {
    font-size: 12px;
    color: #94a3b8;
}
QLabel#mutedLabel {
    color: #64748b;
    font-size: 11px;
}
"""
