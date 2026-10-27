from PyQt6.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout, QWidget

from .theme import Palette, kpi_card_qss


class KpiCard(QFrame):
    def __init__(self, title: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("KpiCard")
        self.setStyleSheet(kpi_card_qss(accent))
        self.setMinimumHeight(72)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(2)

        self._value = QLabel("0")
        self._value.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {accent};"
        )

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-size: 11px; color: {Palette.TEXT_DIM}; "
            "text-transform: uppercase; letter-spacing: 0.5px;"
        )

        layout.addWidget(self._value)
        layout.addWidget(title_lbl)

    def set_value(self, value):
        self._value.setText(str(value))

# Собирает пару подпись + выпадающий список в один контейнер.
def make_filter_field(
    label: str, width: int
) -> tuple[QComboBox, QWidget]:
    box = QVBoxLayout()
    box.setSpacing(2)

    lbl = QLabel(label)
    lbl.setObjectName("FieldLabel")

    combo = QComboBox()
    combo.setFixedWidth(width)

    box.addWidget(lbl)
    box.addWidget(combo)

    wrapper = QWidget()
    wrapper.setLayout(box)
    return combo, wrapper
