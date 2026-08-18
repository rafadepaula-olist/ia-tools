from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Clique para ativar/desativar")

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.update()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track background
        track_color = QColor("#10b981") if self._checked else QColor("#333a4d")
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(0, 0, self.width(), self.height())
        painter.drawRoundedRect(rect, self.height() / 2, self.height() / 2)

        # Handle circle
        circle_radius = (self.height() - 6) / 2
        circle_x = self.width() - circle_radius - 5 if self._checked else 5 + circle_radius
        circle_y = self.height() / 2

        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(QPointF(circle_x, circle_y), circle_radius, circle_radius)
        painter.end()
