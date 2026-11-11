# type: ignore
from typing import ClassVar

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .theme import DETAIL_CARD_QSS, TABLE_QSS, Palette, kpi_card_qss


# Виджет ключевого показателя
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
        self._value.setStyleSheet(f"font-size: 22px; font-weight: 600; color: {accent};")

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-size: 11px; color: {Palette.TEXT_DIM}; "
            "text-transform: uppercase; letter-spacing: 0.5px;"
        )

        layout.addWidget(self._value)
        layout.addWidget(title_lbl)

    def set_value(self, value):
        self._value.setText(str(value))

# Собирает пару подпись + комбо-бокс
def make_filter_field(label: str, width: int) -> tuple[QComboBox, QWidget]:
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

# Карточка с подробной информацией о выбранной аномалии
class DetailCard(QFrame):
    PRIORITY: ClassVar[list[str]] = [
        "Номер трубы", "Регион", "Год обследования", "Всего дефектов",
        "Макс. глубина, %", "Класс (a)", "Класс (b)", "Класс (c)",
        "Длина трубы, м", "Толщина, мм", "Расстояние, м",
        "Характер особенности", "Глубина, %", "Расположение", "Опасность",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailCard")
        self.setStyleSheet(DETAIL_CARD_QSS)
        self.setMinimumWidth(340)
        self.setMaximumWidth(480)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(16, 16, 16, 16)
        main_lay.setSpacing(12)

        self._title = QLabel("Детали аномалии")
        self._title.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {Palette.TEXT};"
        )
        main_lay.addWidget(self._title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")

        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_content)
        main_lay.addWidget(self.scroll_area)

        self.clear()

    #Полностью очищает layout
    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    # Очищает карточку и показывает заглушку
    def clear(self):
        self._clear_content()
        self._title.setText("Детали аномалии")
        placeholder = QLabel("Выберите строку в таблице")
        placeholder.setStyleSheet(f"color: {Palette.TEXT_DIM}; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(placeholder)

    # Заполняет карточку данными из словаря с приоритетом полей
    def set_data(self, data: dict):
        self._clear_content()
        if not data:
            self.clear()
            return

        pipe = data.get("Номер трубы")
        if pipe and pipe != "Нет данных":
            self._title.setText(f"Аномалия — Труба {pipe}")
        else:
            self._title.setText("Детали аномалии")

        ordered_keys = [k for k in self.PRIORITY if k in data]
        other_keys = [k for k in data if k not in self.PRIORITY]

        for key in ordered_keys + other_keys:
            val = data[key]

            row_widget = QWidget()
            row_lay = QVBoxLayout(row_widget)
            row_lay.setContentsMargins(0, 4, 0, 4)
            row_lay.setSpacing(2)

            lbl_key = QLabel(key.upper())
            lbl_key.setStyleSheet(
                f"color: {Palette.TEXT_DIM}; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;"
            )
            lbl_key.setWordWrap(True)

            lbl_val = QLabel(str(val))
            lbl_val.setWordWrap(True)

            if val == "Нет данных":
                lbl_val.setStyleSheet(
                    f"color: {Palette.TEXT_DIM}; font-size: 13px; font-style: italic;"
                )
            else:
                lbl_val.setStyleSheet(
                    f"color: {Palette.TEXT}; font-size: 13px;"
                )

            row_lay.addWidget(lbl_key)
            row_lay.addWidget(lbl_val)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color: {Palette.BORDER}; background-color: {Palette.BORDER}; max-height: 1px;")
            row_lay.addWidget(sep)

            self.content_layout.addWidget(row_widget)

# Виджет таблицы данных
#
class DataTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(32)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)

        self.setStyleSheet(TABLE_QSS)
