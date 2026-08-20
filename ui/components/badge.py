from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

class Badge(QLabel):
    COLORS = {
        "active": ("#064e3b", "#34d399", "#065f46"),
        "inactive": ("#381419", "#f87171", "#561d25"),
        "shelved": ("#3b2308", "#fbbf24", "#5c380d"),
        "stdio": ("#181b34", "#a5b4fc", "#2a2f54"),
        "http": ("#0a2838", "#38bdf8", "#12435c"),
        "sse": ("#27123d", "#c084fc", "#431e67"),
        "plugin": ("#0b312b", "#2dd4bf", "#134e44"),
        "skill": ("#36190a", "#fb923c", "#56270f"),
        "extension": ("#1c1b3f", "#818cf8", "#2f2d65"),
        "remote": ("#0a2838", "#38bdf8", "#12435c"),
        "local": ("#1a202c", "#94a3b8", "#2d3748"),
        "project": ("#24143d", "#c084fc", "#3f236b"),
        "global": ("#0a2e23", "#6ee7b7", "#134e3b"),
        "cloud": ("#32112d", "#f472b6", "#521d4a"),
    }

    def __init__(self, text: str, variant: str = "stdio", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_variant(variant, text=text)

    def set_variant(self, variant: str, text: str = None):
        v_key = variant.lower()
        if text is not None:
            raw_text = text.upper()
            if v_key == "active":
                raw_text = "● Ativo"
            elif v_key == "inactive":
                raw_text = "● Inativo"
            elif v_key == "shelved":
                raw_text = "● Temporário"
            self.setText(raw_text)

        bg, text_color, border_color = self.COLORS.get(v_key, ("#1a202c", "#94a3b8", "#2d3748"))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 2px 7px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)
