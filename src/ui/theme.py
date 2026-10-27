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

EXTRA_GROUP_QSS = f"""
    QFrame#ExtraGroup {{
        background-color: {Palette.PANEL};
        border: 1px solid {Palette.BORDER};
        border-radius: 6px;
    }}
"""

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

TABLE_QSS = f"""
    QTableView {{
        background-color: {Palette.PANEL};
        alternate-background-color: {Palette.PANEL_ALT};
        color: {Palette.TEXT};
        selection-background-color: {Palette.ACCENT};
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
