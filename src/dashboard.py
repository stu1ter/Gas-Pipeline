import pandas as pd
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from analytics import AnalyticsEngine
from ui.charts import ChartRenderer
from ui.overlay import LoadingOverlay
from ui.table_manager import TableManager
from ui.theme import (
    APPLY_BUTTON_QSS,
    EXTRA_GROUP_QSS,
    FILTER_PANEL_QSS,
    SORT_BUTTON_QSS,
    TAB_WIDGET_QSS,
    Palette,
)
from ui.widgets import DetailCard, KpiCard, make_filter_field


# Инициализирует главное окно и загружает данные
class DashboardWindow(QMainWindow):
    # Инициализирует главное окно и загружает данные
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

    # Собирает основной каркас интерфейса
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

    # Создает панель с фильтрами
    def _build_filters(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("FilterPanel")
        panel.setStyleSheet(FILTER_PANEL_QSS)

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        filters_row = QHBoxLayout()
        filters_row.setSpacing(16)

        main_group = QWidget()
        main_lay = QHBoxLayout(main_group)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(12)

        self.combo_region, region_w = make_filter_field("Участок", 240)
        self.combo_region.currentIndexChanged.connect(self._on_region_changed)
        main_lay.addWidget(region_w)

        self.combo_year, year_w = make_filter_field("Год", 100)
        main_lay.addWidget(year_w)

        filters_row.addWidget(main_group)

        extra_group = QFrame()
        extra_group.setObjectName("ExtraGroup")
        extra_group.setStyleSheet(EXTRA_GROUP_QSS)
        extra_lay = QHBoxLayout(extra_group)
        extra_lay.setContentsMargins(12, 8, 12, 10)
        extra_lay.setSpacing(12)

        self.combo_loc, loc_w = make_filter_field("Расположение", 180)
        extra_lay.addWidget(loc_w)

        self.combo_haz, haz_w = make_filter_field("Опасность", 100)
        extra_lay.addWidget(haz_w)

        filters_row.addWidget(extra_group)
        filters_row.addStretch()

        outer.addLayout(filters_row)
        outer.addLayout(self._build_apply_button())

        return panel

    # Создает кнопку применения фильтров
    def _build_apply_button(self) -> QVBoxLayout:
        btn_box = QVBoxLayout()
        btn_box.setContentsMargins(0, 16, 0, 0)

        self.btn_apply = QPushButton("Применить фильтры")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setFixedHeight(34)
        self.btn_apply.setMaximumWidth(200)
        self.btn_apply.setStyleSheet(APPLY_BUTTON_QSS)
        self.btn_apply.clicked.connect(self.update_dashboard)

        btn_box.addWidget(self.btn_apply)
        btn_box.addStretch()

        return btn_box

    # Создает панель с KPI-карточками
    def _build_kpi_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.kpi_total = KpiCard("Всего дефектов", Palette.KPI_BLUE)
        self.kpi_replacement = KpiCard("Требуют замены", Palette.KPI_ORANGE)
        self.kpi_max = KpiCard("Макс. глубина", Palette.KPI_RED)
        self.kpi_unique = KpiCard("Уникальных типов", Palette.KPI_PURPLE)
        for card in (self.kpi_total, self.kpi_replacement, self.kpi_max, self.kpi_unique):
            row.addWidget(card)
        return row

    # Создает вертикальный разделитель для графиков и таблиц
    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_charts())
        splitter.addWidget(self._build_table())
        splitter.setSizes([350, 400])
        return splitter

    # Создает контейнер для графиков
    def _build_charts(self) -> QWidget:
        w = QWidget()
        w.setMinimumHeight(280)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.chart_renderer = ChartRenderer(
            on_defect_clicked=self._on_chart_defect_clicked,
            on_class_clicked=self._on_chart_class_clicked
        )

        for canvas in self.chart_renderer.get_canvases():
            lay.addWidget(canvas)

        return w

    # Создает контейнер для таблиц и карточки деталей
    def _build_table(self) -> QWidget:
        w = QWidget()
        outer_lay = QHBoxLayout(w)
        outer_lay.setContentsMargins(0, 4, 0, 0)
        outer_lay.setSpacing(12)

        self.detail_card = DetailCard()
        outer_lay.addWidget(self.detail_card, stretch=1)

        self.table_tabs = QTabWidget()
        self.table_tabs.setStyleSheet(TAB_WIDGET_QSS)
        self.table_tabs.setTabsClosable(True)
        self.table_tabs.setMovable(False)

        self.table_manager = TableManager(self.table_tabs, self.detail_card)
        self.table_manager.setup_base_tabs()

        self.table_tabs.tabCloseRequested.connect(self.table_manager.close_tab)
        tab_bar = self.table_tabs.tabBar()

        if tab_bar is not None:
            tab_bar.installEventFilter(self)
        self.table_tabs.currentChanged.connect(self._on_tab_changed)

        self.btn_reset_sort = QPushButton("Сортировка по умолчанию")
        self.btn_reset_sort.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_sort.setStyleSheet(SORT_BUTTON_QSS)
        self.btn_reset_sort.clicked.connect(
            lambda: self.table_manager.reset_sorting(self.table_tabs.currentIndex())
        )
        self.table_tabs.setCornerWidget(self.btn_reset_sort, Qt.Corner.TopRightCorner)

        outer_lay.insertWidget(0, self.table_tabs, stretch=4)
        return w

    # Заполняет начальные значения фильтров
    def _load_initial_filters(self):
        regions = sorted(self.full_df["Регион"].dropna().unique())
        self.combo_region.blockSignals(True)
        self.combo_region.clear()
        self.combo_region.addItems(regions)
        self.combo_region.blockSignals(False)

        self._on_region_changed()
        self.update_dashboard()

    # Обновляет список годов при смене региона
    def _on_region_changed(self):
        region = self.combo_region.currentText()
        df_region = self.full_df.loc[self.full_df["Регион"] == region]
        years = sorted(
            str(int(y)) for y in df_region["Год обследования"].dropna().unique()
        )

        self.combo_year.blockSignals(True)
        self.combo_year.clear()
        self.combo_year.addItems(years)
        self.combo_year.blockSignals(False)

        self._update_other_filters(df_region)

    # Обновляет списки расположений и классов опасности
    def _update_other_filters(self, df: pd.DataFrame):
        self.combo_loc.blockSignals(True)
        self.combo_haz.blockSignals(True)

        self.combo_loc.clear()
        self.combo_loc.addItem("Все", "Все")
        for loc in sorted(df["Расположение"].dropna().unique()):
            self.combo_loc.addItem(AnalyticsEngine.LOC_MAP.get(loc, loc), loc)

        self.combo_haz.clear()
        self.combo_haz.addItem("Все", "Все")
        valid = [h for h in df["Опасность"].dropna().unique() if h in ["(a)", "(b)", "(c)"]]
        for haz in sorted(valid):
            self.combo_haz.addItem(haz, haz)

        self.combo_loc.blockSignals(False)
        self.combo_haz.blockSignals(False)

    # Обновляет весь дашборд с отображением оверлея загрузки
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

    # Выполняет фильтрацию данных и обновление всех компонентов
    def _perform_update(self):
        region = self.combo_region.currentText()
        year_str = self.combo_year.currentText()
        if not region or not year_str:
            return

        year = float(year_str)
        df_geo = self.full_df[
            (self.full_df["Регион"] == region) & (self.full_df["Год обследования"] == year)
        ]

        filters = {
            "Расположение": self.combo_loc.currentData(),
            "Опасность": self.combo_haz.currentData(),
        }

        self.engine = AnalyticsEngine(df_geo) # type: ignore
        self.current_df = self.engine.filter_data(filters)
        self.engine.df = self.current_df

        while self.table_tabs.count() > 2:
            self.table_tabs.removeTab(2)
        self.table_manager.custom_tables.clear()
        self.table_tabs.setCurrentIndex(0)

        self._refresh_kpi()
        self.chart_renderer.redraw_all(self.engine, self.current_df)
        self.table_manager.update_tables(self.engine)

    # Обновляет значения KPI-карточек
    def _refresh_kpi(self):
        k = self.engine.get_kpis()
        self.kpi_total.set_value(k["total"])
        self.kpi_replacement.set_value(k["pipes_replacement"])
        self.kpi_max.set_value(f"{k['max_depth']} %")
        self.kpi_unique.set_value(k["unique_defects"])

    # Ресайзим оверлей при изменении размера главного окна
    def resizeEvent(self, event):
        super().resizeEvent(event)

        central = self.centralWidget()
        if central and hasattr(self, '_overlay') and self._overlay:
            self._overlay.setGeometry(central.rect())
            self._overlay.raise_()

    # Обрабатывает клик средней кнопкой мыши по вкладкам
    def eventFilter(self, obj, event):
        tab_bar = self.table_tabs.tabBar()
        if (
            tab_bar is not None
            and obj == tab_bar
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.MiddleButton
        ):
            index = tab_bar.tabAt(event.position().toPoint())
            if index >= 0:
                self.table_manager.close_tab(index)
                return True
        return super().eventFilter(obj, event)

    # Обновляет карточку деталей при переключении вкладок
    def _on_tab_changed(self, index):
        self.table_manager.refresh_detail_for_tab(index)

    # Создает вкладку с отфильтрованными данными по типу дефекта
    def _on_chart_defect_clicked(self, label):
        if label == "Другие":
            return
        filtered_df = self.current_df[self.current_df["Характер особенности"] == label]
        self.table_manager.create_filtered_tab(label, filtered_df)

    # Создает вкладку с отфильтрованными данными по классу опасности
    def _on_chart_class_clicked(self, label):
        tab_name = f"Класс {label}"
        filtered_df = self.current_df[self.current_df["Опасность"] == label]
        self.table_manager.create_filtered_tab(tab_name, filtered_df)
