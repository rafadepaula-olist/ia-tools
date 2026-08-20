from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Clique para alternar status")

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
        track_color = QColor("#4c6fe7") if self._checked else QColor("#222838")
        border_color = QColor("#5c7df0") if self._checked else QColor("#333b50")
        
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        radius = (self.height() - 2) / 2
        
        painter.setBrush(QBrush(track_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, radius, radius)

        # Handle circle (knob)
        circle_radius = (self.height() - 7) / 2
        circle_x = self.width() - circle_radius - 4 if self._checked else 4 + circle_radius
        circle_y = self.height() / 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(QPointF(circle_x, circle_y), circle_radius, circle_radius)
        
        # Subtle dot or check inside knob
        if self._checked:
            painter.setBrush(QBrush(QColor("#4c6fe7")))
            painter.drawEllipse(QPointF(circle_x, circle_y), 2.5, 2.5)

        painter.end()
