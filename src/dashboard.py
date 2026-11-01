import pandas as pd
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from analytics import AnalyticsEngine
from data import PandasModel
from ui.charts import ChartRenderer
from ui.overlay import LoadingOverlay
from ui.theme import (
    APPLY_BUTTON_QSS,
    EXTRA_GROUP_QSS,
    FILTER_PANEL_QSS,
    TABLE_MODE_QSS,
    Palette,
)
from ui.widgets import DataTable, DetailCard, KpiCard, make_filter_field


class DashboardWindow(QMainWindow):
    def __init__(self, full_df: pd.DataFrame):
        super().__init__()
        self.setWindowTitle("Gas Pipeline")
        self.resize(1400, 900)

        self.full_df = full_df
        self.current_df = full_df.copy()
        self.engine = AnalyticsEngine(self.current_df)
        self._is_updating = False

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

        self._overlay = LoadingOverlay(central, "Загрузка данных…")

    # Верхняя панель
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

    # Основные фильтры
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

    # Дополнительные фильтры
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

    # Кнопака Применить фильтры
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

    # Панель с ключевыми показателями
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

    # Вертикальный разделитель
    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_charts())
        splitter.addWidget(self._build_table())
        splitter.setSizes([350, 400])
        return splitter

    # Внедрение графиков
    def _build_charts(self) -> QWidget:
        w = QWidget()
        w.setMinimumHeight(280)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.chart_renderer = ChartRenderer()

        for canvas in self.chart_renderer.get_canvases():
            lay.addWidget(canvas)

        return w

    # Сборка блока с таблицец
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
        self.table_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {Palette.TEXT};"
        )
        header_lay.addWidget(self.table_label)
        header_lay.addStretch()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Все аномалии", "Топ-10 по глубине"])
        self.mode_combo.setStyleSheet(TABLE_MODE_QSS)
        self.mode_combo.currentIndexChanged.connect(self._refresh_table)
        header_lay.addWidget(self.mode_combo)

        table_lay.addLayout(header_lay)

        self.table = DataTable()
        table_lay.addWidget(self.table)

        outer_lay.addWidget(table_container, stretch=4)

        self.detail_card = DetailCard()
        outer_lay.addWidget(self.detail_card, stretch=1)

        return w

    # Загрузка начальных фильтров
    def _load_initial_filters(self):
        regions = sorted(self.full_df["Регион"].dropna().unique())
        self.combo_region.blockSignals(True)
        self.combo_region.clear()
        self.combo_region.addItems(regions)
        self.combo_region.blockSignals(False)

        self._on_region_changed()
        self.update_dashboard()

    # Обновление годов при изменении регион
    def _on_region_changed(self):
        region = self.combo_region.currentText()
        df_region = self.full_df.loc[self.full_df["Регион"] == region]
        years = sorted(
            str(int(y)) for y in df_region["Год обследования"].dropna().unique() # type: ignore
        )

        self.combo_year.blockSignals(True)
        self.combo_year.clear()
        self.combo_year.addItems(years)
        self.combo_year.blockSignals(False)

        self._update_other_filters(df_region)

    # Обновление остальных фильтров при изменении региона
    def _update_other_filters(self, df: pd.DataFrame):
        self.combo_loc.blockSignals(True)
        self.combo_haz.blockSignals(True)

        self.combo_loc.clear()
        self.combo_loc.addItem("Все", "Все")
        for loc in sorted(df["Расположение"].dropna().unique()):
            self.combo_loc.addItem(AnalyticsEngine.LOC_MAP.get(loc, loc), loc)

        self.combo_haz.clear()
        self.combo_haz.addItem("Все", "Все")
        valid = [
            h for h in df["Опасность"].dropna().unique()
            if h in ["(a)", "(b)", "(c)"]
        ]
        for haz in sorted(valid):
            self.combo_haz.addItem(haz, haz)

        self.combo_loc.blockSignals(False)
        self.combo_haz.blockSignals(False)

    # Триггер при нажатии на кнопку
    def update_dashboard(self):
        if self._is_updating:
            return
        self._is_updating = True
        self.btn_apply.setEnabled(False)

        self._overlay.set_text("Загрузка данных…")
        central = self.centralWidget()
        if central:
            self._overlay.setGeometry(central.rect())
        self._overlay.raise_()
        self._overlay.show()

        QApplication.processEvents()

        try:
            self._perform_update()
        finally:
            self._overlay.hide()
            self.btn_apply.setEnabled(True)
            self._is_updating = False

    # Пересчитывает данные при обновлении фильтров
    def _perform_update(self):
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

        self.engine = AnalyticsEngine(df_geo) # type: ignore
        self.current_df = self.engine.filter_data(filters)
        self.engine.df = self.current_df

        self._refresh_kpi()

        self.chart_renderer.redraw_all(self.engine, self.current_df)

        self._refresh_table()

    # Пересчитывает ключевые показатели
    def _refresh_kpi(self):
        k = self.engine.get_kpis()
        self.kpi_total.set_value(k["total"])
        self.kpi_avg.set_value(f"{k['avg_depth']} %")
        self.kpi_max.set_value(f"{k['max_depth']} %")
        self.kpi_unique.set_value(k["unique_defects"])

    # Обновление таблицы
    def _refresh_table(self, _=None):
        selection_model = self.table.selectionModel()
        if selection_model is not None:
            try:
                selection_model.selectionChanged.disconnect()
            except TypeError:
                pass

        mode = self.mode_combo.currentIndex()
        display = self.engine.get_table_data(mode=mode, top_n=10)

        if display.empty:
            self.table.setModel(PandasModel(pd.DataFrame(columns=["Нет данных"])))
            self.table_label.setText("Нет данных")
            self.detail_card.clear()
            return

        self.table_label.setText("Все аномалии" if mode == 0 else "Топ-10 по глубине")

        source_model = PandasModel(display)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(source_model)
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)

        self.table.setModel(self.proxy_model)

        visible_cols_count = 6
        for i in range(visible_cols_count, len(display.columns)):
            self.table.setColumnHidden(i, True)

        self.table.resizeColumnsToContents()

        header = self.table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(False)

            if visible_cols_count > 0:
                last_idx = visible_cols_count - 1
                for i in range(visible_cols_count):
                    if i == last_idx:
                        header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                    else:
                        header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        new_selection_model = self.table.selectionModel()
        if new_selection_model is not None:
            new_selection_model.selectionChanged.connect(self._on_row_selected)

        if self.proxy_model.rowCount() > 0:
            self.table.selectRow(0)
        else:
            self.detail_card.clear()

    # Отправляет данные строки в карточку аномалии
    def _on_row_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            self.detail_card.clear()
            return

        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        row = source_index.row()
        model = self.proxy_model.sourceModel()

        if hasattr(model, 'get_row_dict'):
            data = model.get_row_dict(row)
            self.detail_card.set_data(data)
        else:
            self.detail_card.clear()
