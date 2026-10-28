# Полупрозрачный оверлей с индикатором загрузки.
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .theme import Palette


class LoadingOverlay(QWidget):
    """Серый слой с надписью, накладывается поверх родителя."""

    def __init__(self, parent: QWidget, text: str = "Загрузка данных…"):
        super().__init__(parent)
        # WA_StyledBackground — чтобы background-color из QSS реально рисовался
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "background-color: rgba(20, 20, 20, 180);"
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel(text)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            f"font-size: 16px; font-weight: 600; "
            f"color: {Palette.TEXT}; "
            f"padding: 24px 40px; "
            f"border-radius: 8px; "
            f"background-color: {Palette.PANEL};"
        )
        layout.addWidget(self._label)

    def set_text(self, text: str):
        self._label.setText(text)

    def paintEvent(self, event):
        # Растягиваемся на весь родитель при каждом показе
        if self.parent():
            self.resize(self.parent().size())
        super().paintEvent(event)
