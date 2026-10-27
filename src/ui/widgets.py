# Переиспользуемые виджеты: KPI-карточка, поле-фильтр, карточка деталей.
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

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


class DetailCard(QFrame):
    """Карточка с подробной информацией о выбранной аномалии."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailCard")
        self.setStyleSheet(f"""
            QFrame#DetailCard {{
                background-color: {Palette.PANEL};
                border: 1px solid {Palette.BORDER};
                border-radius: 6px;
            }}
        """)
        # Делаем карточку чуть шире для комфортного чтения
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

        # Область прокрутки для содержимого
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")

        # Используем QVBoxLayout вместо QFormLayout, чтобы избежать наложения текста
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)

        self.scroll.setWidget(self.scroll_content)
        main_lay.addWidget(self.scroll)

        self.clear()

    def _clear_content(self):
        """Полностью очищает layout."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def clear(self):
        """Очищает карточку и показывает заглушку."""
        self._clear_content()
        placeholder = QLabel("Выберите строку в таблице")
        placeholder.setStyleSheet(f"color: {Palette.TEXT_DIM}; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(placeholder)

    def set_data(self, data: dict):
        """Заполняет карточку данными из словаря (вертикальный список)."""
        self._clear_content()
        if not data:
            self.clear()
            return

        for key, val in data.items():
            # Контейнер для одной пары (Ключ + Значение)
            row_widget = QWidget()
            row_lay = QVBoxLayout(row_widget)
            row_lay.setContentsMargins(0, 4, 0, 4)
            row_lay.setSpacing(2)

            # Заголовок поля (мелкий, серый, капсом для стиля)
            lbl_key = QLabel(key.upper())
            lbl_key.setStyleSheet(
                f"color: {Palette.TEXT_DIM}; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;"
            )
            lbl_key.setWordWrap(True)

            # Значение (крупное, белое)
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

            # Тонкий разделитель
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color: {Palette.BORDER}; background-color: {Palette.BORDER}; max-height: 1px;")
            row_lay.addWidget(sep)

            self.content_layout.addWidget(row_widget)
