from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .theme import OVERLAY_LABEL_QSS, OVERLAY_QSS


# Полупрозрачный оверлей с индикатором загрузки.
class LoadingOverlay(QWidget):
    def __init__(self, parent: QWidget, text: str = "Загрузка данных…"):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(OVERLAY_QSS)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel(text)
        self._label.setStyleSheet(OVERLAY_LABEL_QSS)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

    def set_text(self, text: str):
        self._label.setText(text)
