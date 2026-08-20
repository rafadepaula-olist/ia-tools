from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta

class SearchBar(QWidget):
    textChanged = pyqtSignal(str)

    def __init__(self, placeholder: str = "Buscar...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: #12151f;
                border: 1px solid #232838;
                border-radius: 6px;
            }
            QFrame:hover {
                border-color: #38425d;
            }
            QFrame:focus-within {
                border-color: #4c6fe7;
                background-color: #151824;
            }
        """)
        c_layout = QHBoxLayout(self.container)
        c_layout.setContentsMargins(8, 2, 6, 2)
        c_layout.setSpacing(6)

        search_icon = QLabel()
        search_icon.setPixmap(qta.icon('fa5s.search', color='#64748b').pixmap(13, 13))
        search_icon.setStyleSheet("background: transparent; border: none;")
        c_layout.addWidget(search_icon)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f1f5f9;
                font-size: 12px;
                padding: 4px 2px;
            }
            QLineEdit:focus {
                border: none;
                background: transparent;
            }
        """)
        self.input.textChanged.connect(self._on_text_changed)
        c_layout.addWidget(self.input, 1)

        # Clear button
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(qta.icon('fa5s.times', color='#64748b'))
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setToolTip("Limpar busca")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #252b3d;
            }
        """)
        self.clear_btn.clicked.connect(self.input.clear)
        self.clear_btn.setVisible(False)
        c_layout.addWidget(self.clear_btn)

        layout.addWidget(self.container)

    def _on_text_changed(self, text: str):
        self.clear_btn.setVisible(bool(text))
        self.textChanged.emit(text)

    def text(self) -> str:
        return self.input.text()

    def setText(self, t: str):
        self.input.setText(t)
