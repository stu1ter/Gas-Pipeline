# Главное окно дашборда
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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
    TABLE_MODE_QSS,
    TABLE_QSS,
    Palette,
)
from ui.widgets import KpiCard, make_filter_field, DetailCard


class DashboardWindow(QMainWindow):
    LOC_MAP = {
        "EXT": "Внешний (EXT)",
        "INT": "Внутренний (INT)",
        "MID": "В теле металла (MID)",
    }

    def __init__(self, full_df: pd.DataFrame):
        super().__init__()
        self.setWindowTitle("Gas Pipeline")
        self.resize(1400, 900)

        self.full_df = full_df
        self.current_df = full_df.copy()
        self.engine = AnalyticsEngine(self.current_df)

        self._init_ui()
        self._load_initial_filters()

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

    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_charts())
        splitter.addWidget(self._build_table())
        splitter.setSizes([350, 400])
        return splitter

    def _build_charts(self) -> QWidget:
        w = QWidget()
        w.setMinimumHeight(280)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.fig_pie = Figure(figsize=(4, 3), dpi=100, constrained_layout=True)
        self.canvas_pie = FigureCanvas(self.fig_pie)
        lay.addWidget(self.canvas_pie)

        self.fig_bar = Figure(figsize=(4, 3), dpi=100, constrained_layout=True)
        self.canvas_bar = FigureCanvas(self.fig_bar)
        lay.addWidget(self.canvas_bar)

        self.fig_top = Figure(figsize=(4, 3), dpi=100, constrained_layout=True)
        self.canvas_top = FigureCanvas(self.fig_top)
        lay.addWidget(self.canvas_top)

        self.chart_renderer = ChartRenderer(self.fig_pie, self.fig_bar, self.fig_top)
        return w

    def _build_table(self) -> QWidget:
        w = QWidget()
        outer_lay = QHBoxLayout(w)
        outer_lay.setContentsMargins(0, 4, 0, 0)
        outer_lay.setSpacing(12)

        table_container = QWidget()
        table_lay = QVBoxLayout(table_container)
        table_lay.setContentsMargins(0, 0, 0, 0)
        table_lay.setSpacing(8)

        header_lay = QHBoxLayout()
        self.table_label = QLabel("Все аномалии")
        self.table_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {Palette.TEXT};")
        header_lay.addWidget(self.table_label)
        header_lay.addStretch()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Все аномалии", "Топ-10 по глубине"])
        self.mode_combo.setStyleSheet(TABLE_MODE_QSS)
        self.mode_combo.currentIndexChanged.connect(self._refresh_table)
        header_lay.addWidget(self.mode_combo)

        table_lay.addLayout(header_lay)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(32)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)

        self.table.setStyleSheet(TABLE_QSS)
        table_lay.addWidget(self.table)

        outer_lay.addWidget(table_container, stretch=4) # Увеличили пропорцию таблицы

        self.detail_card = DetailCard()
        outer_lay.addWidget(self.detail_card, stretch=1) # Карточка занимает свою минимальную ширину

        return w

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
        years = sorted(str(int(y)) for y in df_region["Год обследования"].dropna().unique())

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
        valid = [h for h in df["Опасность"].dropna().unique() if h in ["(a)", "(b)", "(c)"]]
        for haz in sorted(valid):
            self.combo_haz.addItem(haz, haz)

        self.combo_loc.blockSignals(False)
        self.combo_haz.blockSignals(False)

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

        self.canvas_pie.draw_idle()
        self.canvas_bar.draw_idle()
        self.canvas_top.draw_idle()

        self._refresh_table()

    def _refresh_kpi(self):
        k = self.engine.get_kpis()
        self.kpi_total.set_value(k["total"])
        self.kpi_avg.set_value(f"{k['avg_depth']} %")
        self.kpi_max.set_value(f"{k['max_depth']} %")
        self.kpi_unique.set_value(k["unique_defects"])

    def _refresh_table(self, _=None):
        if self.table.selectionModel():
            try:
                self.table.selectionModel().selectionChanged.disconnect()
            except TypeError:
                pass

        if self.current_df.empty:
            self.table.setModel(PandasModel(pd.DataFrame(columns=["Нет данных"])))
            self.table_label.setText("Нет данных")
            self.detail_card.clear()
            return

        visible_cols = ["Номер трубы", "Расстояние, м", "Глубина, %",
                        "Характер особенности", "Расположение", "Опасность"]
        visible_cols = [c for c in visible_cols if c in self.current_df.columns]

        valid = self.current_df.dropna(subset=["Глубина, %", "Номер трубы"])
        if valid.empty:
            self.table.setModel(PandasModel(pd.DataFrame(columns=["Нет данных"])))
            self.table_label.setText("Нет данных")
            self.detail_card.clear()
            return

        valid = valid.sort_values(by="Глубина, %", ascending=False).reset_index(drop=True)
        mode = self.mode_combo.currentIndex()

        if mode == 0:
            self.table_label.setText("Все аномалии")
            display = valid
        else:
            self.table_label.setText("Топ-10 по глубине")
            display = valid.head(10).copy()

        other_cols = [c for c in display.columns if c not in visible_cols]
        display = display[visible_cols + other_cols]

        model = PandasModel(display)
        self.table.setModel(model)

        for i in range(len(visible_cols), len(display.columns)):
            self.table.setColumnHidden(i, True)

        self.table.resizeColumnsToContents()

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)

        if len(visible_cols) > 0:
            last_idx = len(visible_cols) - 1
            for i in range(len(visible_cols)):
                if i == last_idx:
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                else:
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.table.selectionModel().selectionChanged.connect(self._on_row_selected)

        if model.rowCount() > 0:
            self.table.selectRow(0)
        else:
            self.detail_card.clear()

    def _on_row_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            self.detail_card.clear()
            return

        row = indexes[0].row()
        model = self.table.model()
        if hasattr(model, 'get_row_dict'):
            data = model.get_row_dict(row)
            self.detail_card.set_data(data)
        else:
            self.detail_card.clear()
