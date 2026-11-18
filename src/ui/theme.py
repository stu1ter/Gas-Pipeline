# Цветовая палитра и QSS-стили.
class Palette:
    BG = "#1e1e1e"
    PANEL = "#252525"
    PANEL_ALT = "#2d2d2d"
    BORDER = "#3a3a3a"
    TEXT = "#e0e0e0"
    TEXT_DIM = "#9a9a9a"
    ACCENT = "#4A90D9"
    ACCENT_HOVER = "#3d7ab8"

    KPI_BLUE = "#4A90D9"
    KPI_ORANGE = "#D9884A"
    KPI_RED = "#D9534F"
    KPI_PURPLE = "#8E7CC3"

# Стиль панели фильтров
FILTER_PANEL_QSS = f"""
    QFrame#FilterPanel {{ background-color: transparent; }}
    QLabel#FieldLabel {{
        color: {Palette.TEXT_DIM};
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 2px;
    }}
    QComboBox {{
        background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
        border: 1px solid {Palette.BORDER};
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 20px;
    }}
    QComboBox:hover {{ border-color: {Palette.ACCENT}; }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox QAbstractItemView {{
        background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
        selection-background-color: {Palette.ACCENT};
        border: 1px solid {Palette.BORDER};
    }}
"""

# Стиль блока дополнительных фильтров
EXTRA_GROUP_QSS = f"""
    QFrame#ExtraGroup {{
        background-color: {Palette.PANEL};
        border: 1px solid {Palette.BORDER};
        border-radius: 6px;
    }}
"""

# Стиль кнопки «Применить фильтры»
APPLY_BUTTON_QSS = f"""
    QPushButton {{
        background-color: {Palette.ACCENT};
        color: white;
        font-weight: 600;
        font-size: 13px;
        padding: 0px 24px;
        border: none;
        border-radius: 4px;
    }}
    QPushButton:hover {{ background-color: {Palette.ACCENT_HOVER}; }}
"""

# Стиль таблицы
TABLE_QSS = f"""
    QTableView {{
        background-color: {Palette.PANEL};
        alternate-background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
        selection-background-color: #555555;
        selection-color: white;
        border: 1px solid {Palette.BORDER};
        border-radius: 6px;
        gridline-color: transparent;
    }}
    QHeaderView::section {{
        background-color: {Palette.BG};
        color: {Palette.TEXT_DIM};
        font-weight: 600;
        font-size: 11px;
        padding: 8px;
        border: none;
        border-bottom: 1px solid {Palette.BORDER};
        border-right: 1px solid {Palette.BORDER};
    }}
    QHeaderView::section:last {{ border-right: none; }}
    QTableCornerButton::section {{
        background-color: {Palette.BG};
        border: none;
    }}
"""

# Стиль для переключателя режима таблицы
TABLE_MODE_QSS = f"""
    QComboBox {{
        background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
        border: 1px solid {Palette.BORDER};
        border-radius: 4px;
        padding: 4px 10px;
        min-width: 170px;
    }}
    QComboBox:hover {{ border-color: {Palette.ACCENT}; }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox QAbstractItemView {{
        background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
        selection-background-color: {Palette.ACCENT};
    }}
"""

# Стиль для KPI-карточки с заданным акцентом
def kpi_card_qss(accent: str) -> str:
    return f"""
        QFrame#KpiCard {{
            background-color: {Palette.PANEL};
            border: 1px solid {Palette.BORDER};
            border-left: 4px solid {accent};
            border-radius: 6px;
        }}
        QLabel {{ border: none; background: transparent; }}
    """

DETAIL_CARD_QSS = f"""
    QFrame#DetailCard {{
        background-color: {Palette.PANEL};
        border: 1px solid {Palette.BORDER};
        border-radius: 6px;
    }}
"""

OVERLAY_QSS = """
    LoadingOverlay {
        background-color: rgba(20, 20, 20, 180);
    }
"""

OVERLAY_LABEL_QSS = f"""
    QLabel {{
        font-size: 16px; font-weight: 600;
        color: {Palette.TEXT};
        padding: 24px 40px;
        border-radius: 8px;
        background-color: {Palette.PANEL};
    }}
"""

# Стили для вкладок
TAB_WIDGET_QSS = f"""
    QTabWidget::pane {{
        border: 1px solid {Palette.BORDER};
        background-color: {Palette.PANEL};
        border-radius: 6px;
        margin-top: -1px;
    }}
    QTabWidget, QTabBar {{
        color: {Palette.TEXT_DIM};
    }}
    QTabBar::tab {{
        background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT_DIM};
        padding: 6px 0px 6px 12px;
        border: 1px solid {Palette.BORDER};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {Palette.PANEL};
        color: {Palette.TEXT_DIM};
        border-bottom: 2px solid {Palette.ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
    }}
"""

# Стиль для кнопки сброса сортировки
SORT_BUTTON_QSS = f"""
    QPushButton {{
        background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
        border: 1px solid {Palette.BORDER};
        border-radius: 4px;
        padding: 4px 12px;
        font-size: 12px;
        margin-left: 10px;
    }}
    QPushButton:hover {{
        border-color: {Palette.ACCENT};
    }}
"""

# Стиль для кнопки закрытия вкладки
CLOSE_BUTTON_QSS = """
    QPushButton {
        background: transparent;
        border: none;
        padding: 0px;
        margin: 0px 2px 0px 0px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 40);
        border-radius: 4px;
    }
"""
