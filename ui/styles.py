DARK_THEME_QSS = """
/* Global App Style */
QMainWindow, QDialog, QWidget {
    background-color: #0c0e14;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #252a3a;
    min-height: 25px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #4c6fe7;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #252a3a;
    min-width: 25px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #4c6fe7;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Main Agent Tab Widget (Flat Modern Underline Tabs) */
QTabWidget::pane {
    border: none;
    background: transparent;
    margin: 0px;
    padding: 0px;
}
QTabBar {
    background: transparent;
    border-bottom: 1px solid #1a1e2b;
}
QTabBar::tab {
    background: transparent;
    color: #94a3b8;
    padding: 8px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
    font-weight: 500;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: transparent;
    color: #ffffff;
    border-bottom: 2px solid #3b82f6;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    color: #f1f5f9;
}

/* Sub Tab Widget (Inside Agent: MCPs vs Plugins/Skills) */
QTabWidget#subTabWidget::pane {
    border: none;
    background: transparent;
    margin: 0px;
    padding: 0px;
}
QTabWidget#subTabWidget QTabBar {
    background: transparent;
    border-bottom: none;
}
QTabWidget#subTabWidget QTabBar::tab {
    background: #141722;
    color: #94a3b8;
    padding: 5px 14px;
    font-size: 12px;
    border: 1px solid #1e2332;
    border-radius: 6px;
    margin-right: 6px;
}
QTabWidget#subTabWidget QTabBar::tab:selected {
    background: #1a2032;
    color: #38bdf8;
    border: 1px solid #38bdf8;
    font-weight: 600;
}
QTabWidget#subTabWidget QTabBar::tab:hover:!selected {
    background: #171b28;
    color: #cbd5e1;
}

/* Scroll Areas */
QScrollArea {
    background: transparent;
    border: none;
}

/* Buttons */
QPushButton {
    background-color: #161924;
    color: #f1f5f9;
    border: 1px solid #242a3a;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #1e2332;
    border-color: #38425d;
}
QPushButton:pressed {
    background-color: #141722;
}
QPushButton:disabled {
    background-color: #11131a;
    color: #475569;
    border-color: #1a1e28;
}

/* Primary Button (Blue / Accent) */
QPushButton#primaryBtn {
    background-color: #3b82f6;
    color: #ffffff;
    border: 1px solid #60a5fa;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #2563eb;
    border-color: #93c5fd;
}
QPushButton#primaryBtn:pressed {
    background-color: #1d4ed8;
}

/* Success Button (Emerald Outline / Mint) */
QPushButton#successBtn {
    background-color: #0b2e22;
    color: #34d399;
    border: 1px solid #10b981;
    font-weight: 600;
}
QPushButton#successBtn:hover {
    background-color: #0f3d2e;
    border-color: #34d399;
}

/* Danger Button (Red) */
QPushButton#dangerBtn {
    background-color: #381419;
    color: #f87171;
    border: 1px solid #ef4444;
    padding: 5px 10px;
}
QPushButton#dangerBtn:hover {
    background-color: #4c1820;
    border-color: #f87171;
}

/* Warning / Amber Button */
QPushButton#warningBtn {
    background-color: #3b2308;
    color: #fbbf24;
    border: 1px solid #f59e0b;
    font-weight: 500;
}
QPushButton#warningBtn:hover {
    background-color: #4d2f0d;
}

/* Secondary Button */
QPushButton#secondaryBtn {
    background-color: #141722;
    color: #cbd5e1;
    border: 1px solid #232838;
}
QPushButton#secondaryBtn:hover {
    background-color: #1c202e;
    color: #ffffff;
    border-color: #353d54;
}

/* Icon Buttons (Minimal square / transparent) */
QPushButton#iconBtn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 3px;
}
QPushButton#iconBtn:hover {
    background-color: #1e2434;
    border-color: #2e384e;
    color: #f1f5f9;
}
QPushButton#iconBtn:pressed {
    background-color: #161b27;
}

QPushButton#editIconBtn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 3px;
}
QPushButton#editIconBtn:hover {
    background-color: #1a2238;
    border-color: #31426d;
    color: #60a5fa;
}

QPushButton#dangerIconBtn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 3px;
}
QPushButton#dangerIconBtn:hover {
    background-color: #381419;
    border-color: #5c1e27;
    color: #f87171;
}

/* Input Fields, Combos & Text Edits */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #12151f;
    color: #f1f5f9;
    border: 1px solid #232838;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #4c6fe7;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #4c6fe7;
    background-color: #151926;
}

QComboBox {
    background-color: #12151f;
    color: #f1f5f9;
    border: 1px solid #232838;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 22px;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #38425d;
}
QComboBox:focus {
    border: 1px solid #4c6fe7;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #151824;
    color: #e2e8f0;
    border: 1px solid #282f42;
    selection-background-color: #242c42;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* Status Bar */
QStatusBar {
    background-color: #0c0e14;
    border-top: 1px solid #161924;
    color: #64748b;
    font-size: 11px;
    padding: 3px 8px;
}

/* Typography & Labels - Strict transparent background */
QLabel {
    background: transparent;
    border: none;
    color: #cbd5e1;
}
QLabel#headerTitle {
    background: transparent;
    border: none;
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
}
QLabel#cardTitle {
    background: transparent;
    border: none;
    font-size: 14px;
    font-weight: 600;
    color: #f8fafc;
}
QLabel#cardSubtitle {
    background: transparent;
    border: none;
    font-size: 12px;
    color: #94a3b8;
}
QLabel#mutedLabel {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 11px;
}
"""
