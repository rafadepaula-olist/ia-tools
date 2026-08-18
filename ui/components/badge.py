from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

class Badge(QLabel):
    COLORS = {
        "active": ("#064e3b", "#34d399", "#059669"),
        "inactive": ("#3f1d24", "#f87171", "#991b1b"),
        "stdio": ("#1e1b4b", "#a5b4fc", "#4f46e5"),
        "http": ("#0c4a6e", "#38bdf8", "#0284c7"),
        "sse": ("#3b0764", "#c084fc", "#7e22ce"),
        "plugin": ("#143e38", "#2dd4bf", "#0d9488"),
        "skill": ("#431407", "#fb923c", "#ea580c"),
        "extension": ("#312e81", "#818cf8", "#4338ca"),
        "remote": ("#0c4a6e", "#38bdf8", "#0284c7"),
        "local": ("#1e293b", "#94a3b8", "#475569"),
    }

    def __init__(self, text: str, variant: str = "stdio", parent=None):
        super().__init__(parent)
        self.setText(text.upper())
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_variant(variant)

    def set_variant(self, variant: str):
        bg, text_color, border_color = self.COLORS.get(variant.lower(), ("#1e293b", "#94a3b8", "#334155"))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
        """)
