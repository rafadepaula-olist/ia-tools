from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta

class SearchBar(QWidget):
    textChanged = pyqtSignal(str)

    def __init__(self, placeholder: str = "Buscar...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.textChanged.connect(self.textChanged.emit)

        # Clear button
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(qta.icon('fa5s.times', color='#64748b'))
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.setToolTip("Limpar busca")
        self.clear_btn.clicked.connect(self.input.clear)
        self.clear_btn.setStyleSheet("QPushButton { background: transparent; border: none; } QPushButton:hover { background: #232736; border-radius: 4px; }")

        layout.addWidget(self.input)
        layout.addWidget(self.clear_btn)

    def text(self) -> str:
        return self.input.text()

    def setText(self, t: str):
        self.input.setText(t)
