# Главное окно дашборда — только композиция UI и связывание с данными.
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from analytics import AnalyticsEngine
from data import PandasModel
from ui.charts import ChartRenderer
from ui.theme import (
    APPLY_BUTTON_QSS,
    EXTRA_GROUP_QSS,
    FILTER_PANEL_QSS,
    TABLE_QSS,
    Palette,
)
from ui.widgets import KpiCard, make_filter_field


class DashboardWindow(QMainWindow):
    LOC_MAP = {
        "EXT": "Внешний (EXT)",
        "INT": "Внутренний (INT)",
        "MID": "В теле металла (MID)",
    }

    def __init__(self, full_df: pd.DataFrame):
        super().__init__()
        self.setWindowTitle("Анализатор аномалий трубопроводов")
        self.resize(1400, 900)

        self.full_df = full_df
        self.current_df = full_df.copy()
        self.engine = AnalyticsEngine(self.current_df)

        self._init_ui()
        self._load_initial_filters()

    # ------------------------------------------------------------ композиция
    def _init_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {Palette.BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        root.addWidget(self._build_filters())
        root.addLayout(self._build_kpi_row())
        root.addWidget(self._build_splitter(), stretch=1)

    # -------------------------------------------------------------- фильтры
    def _build_filters(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("FilterPanel")
        panel.setStyleSheet(FILTER_PANEL_QSS)

        outer = QHBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(16)

        outer.addWidget(self._build_main_group())
        outer.addWidget(self._build_extra_group())
        outer.addStretch()
        outer.addLayout(self._build_apply_button())

        return panel

    def _build_main_group(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.combo_region, region_w = make_filter_field("Участок", 240)
        self.combo_region.currentIndexChanged.connect(self._on_region_changed)
        lay.addWidget(region_w)

        self.combo_year, year_w = make_filter_field("Год", 100)
        lay.addWidget(year_w)

        return w

    def _build_extra_group(self) -> QFrame:
        w = QFrame()
        w.setObjectName("ExtraGroup")
        w.setStyleSheet(EXTRA_GROUP_QSS)

        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 8, 12, 10)
        lay.setSpacing(12)

        self.combo_loc, loc_w = make_filter_field("Расположение", 180)
        lay.addWidget(loc_w)

        self.combo_haz, haz_w = make_filter_field("Опасность", 100)
        lay.addWidget(haz_w)

        return w

    def _build_apply_button(self) -> QVBoxLayout:
        btn_box = QVBoxLayout()
        btn_box.setContentsMargins(0, 16, 0, 0)

        self.btn_apply = QPushButton("Применить фильтры")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setFixedHeight(34)
        self.btn_apply.setStyleSheet(APPLY_BUTTON_QSS)
        self.btn_apply.clicked.connect(self.update_dashboard)

        btn_box.addWidget(self.btn_apply)
        return btn_box

    # ----------------------------------------------------------------- KPI
    def _build_kpi_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.kpi_total = KpiCard("Всего дефектов", Palette.KPI_BLUE)
        self.kpi_avg = KpiCard("Средняя глубина", Palette.KPI_ORANGE)
        self.kpi_max = KpiCard("Макс. глубина", Palette.KPI_RED)
        self.kpi_unique = KpiCard("Уникальных типов", Palette.KPI_PURPLE)
        for card in (self.kpi_total, self.kpi_avg,
                     self.kpi_max, self.kpi_unique):
            row.addWidget(card)
        return row

    # ------------------------------------------------------------- Splitter
    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._build_charts())
        splitter.addWidget(self._build_table())
        splitter.setSizes([420, 320])
        return splitter

    def _build_charts(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.fig_pie = Figure(figsize=(4, 3), dpi=100)
        self.canvas_pie = FigureCanvas(self.fig_pie)
        lay.addWidget(self.canvas_pie)

        self.fig_bar = Figure(figsize=(4, 3), dpi=100)
        self.canvas_bar = FigureCanvas(self.fig_bar)
        lay.addWidget(self.canvas_bar)

        self.fig_top = Figure(figsize=(4, 3), dpi=100)
        self.canvas_top = FigureCanvas(self.fig_top)
        lay.addWidget(self.canvas_top)

        self.chart_renderer = ChartRenderer(
            self.fig_pie, self.fig_bar, self.fig_top
        )
        return w

    def _build_table(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)

        lbl = QLabel("10 самых опасных дефектов (по глубине)")
        lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {Palette.TEXT};"
        )
        lay.addWidget(lbl)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setStyleSheet(TABLE_QSS)
        lay.addWidget(self.table)
        return w

    # ------------------------------------------------------ фильтры: данные
    def _load_initial_filters(self):
        regions = sorted(self.full_df["Регион"].dropna().unique())
        self.combo_region.blockSignals(True)
        self.combo_region.clear()
        self.combo_region.addItems(regions)
        self.combo_region.blockSignals(False)

        self._on_region_changed()
        self.update_dashboard()

    def _on_region_changed(self):
        region = self.combo_region.currentText()
        df_region = self.full_df[self.full_df["Регион"] == region]
        years = sorted(
            str(int(y)) for y in df_region["Год обследования"].dropna().unique()
        )

        self.combo_year.blockSignals(True)
        self.combo_year.clear()
        self.combo_year.addItems(years)
        self.combo_year.blockSignals(False)

        self._update_other_filters(df_region)

    def _update_other_filters(self, df: pd.DataFrame):
        self.combo_loc.blockSignals(True)
        self.combo_haz.blockSignals(True)

        self.combo_loc.clear()
        self.combo_loc.addItem("Все", "Все")
        for loc in sorted(df["Расположение"].dropna().unique()):
            self.combo_loc.addItem(self.LOC_MAP.get(loc, loc), loc)

        self.combo_haz.clear()
        self.combo_haz.addItem("Все", "Все")
        valid = [h for h in df["Опасность"].dropna().unique()
                 if h in ["(a)", "(b)", "(c)"]]
        for haz in sorted(valid):
            self.combo_haz.addItem(haz, haz)

        self.combo_loc.blockSignals(False)
        self.combo_haz.blockSignals(False)

    # ---------------------------------------------------------- обновление
    def update_dashboard(self):
        region = self.combo_region.currentText()
        year_str = self.combo_year.currentText()
        if not region or not year_str:
            return

        year = float(year_str)
        df_geo = self.full_df[
            (self.full_df["Регион"] == region)
            & (self.full_df["Год обследования"] == year)
        ]

        filters = {
            "Расположение": self.combo_loc.currentData(),
            "Опасность": self.combo_haz.currentData(),
        }

        self.engine = AnalyticsEngine(df_geo)
        self.current_df = self.engine.filter_data(filters)
        self.engine.df = self.current_df

        self._refresh_kpi()
        self.chart_renderer.redraw_all(self.engine, self.current_df)
        self.canvas_pie.draw()
        self.canvas_bar.draw()
        self.canvas_top.draw()
        self._refresh_table()

    def _refresh_kpi(self):
        k = self.engine.get_kpis()
        self.kpi_total.set_value(k["total"])
        self.kpi_avg.set_value(f"{k['avg_depth']} %")
        self.kpi_max.set_value(f"{k['max_depth']} %")
        self.kpi_unique.set_value(k["unique_defects"])

    def _refresh_table(self):
        if self.current_df.empty:
            self.table.setModel(
                PandasModel(pd.DataFrame(columns=["Нет данных"]))
            )
            return

        cols = ["Номер трубы", "Расстояние, м", "Глубина, %",
                "Характер особенности", "Расположение", "Опасность"]
        cols = [c for c in cols if c in self.current_df.columns]

        valid = self.current_df.dropna(subset=["Глубина, %", "Номер трубы"])
        top10 = valid.sort_values(by="Глубина, %", ascending=False).head(10)

        display = top10[cols].copy()
        if "Расстояние, м" in display.columns:
            display["Расстояние, м"] = display["Расстояние, м"].round(2)
        if "Глубина, %" in display.columns:
            display["Глубина, %"] = display["Глубина, %"].round(1)

        self.table.setModel(PandasModel(display))
