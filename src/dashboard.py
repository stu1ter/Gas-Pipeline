# Главное окно дашборда."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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


# Карточка ключевого показателя
class KpiCard(QFrame):
    def __init__(self, title: str, color: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background-color: {color}; border-radius: 10px; padding: 10px; }}"
            "QLabel { color: white; border: none; }"
        )
        layout = QVBoxLayout(self)

        self._value = QLabel("0")
        self._value.setStyleSheet("font-size: 24px; font-weight: bold;")
        self._value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._value)
        layout.addWidget(title_lbl)

    def set_value(self, value):
        self._value.setText(str(value))

# Отрисовка всех графиков
class ChartRenderer:
    DARK_BG = "#2b2b2b"
    SPINE = "#444444"

    def __init__(self, fig_pie: Figure, fig_bar: Figure, fig_top: Figure):
        self.fig_pie = fig_pie
        self.fig_bar = fig_bar
        self.fig_top = fig_top

    # Перерисовка при обновлении данных
    def redraw_all(self, engine: AnalyticsEngine, current_df: pd.DataFrame):
        self._draw_defect_types(engine)
        self._draw_depth_hist(engine)
        self._draw_top_pipes(current_df)

    # Единый стиль оформления графиков
    def _theme(self, ax, title):
        ax.set_facecolor(self.DARK_BG)
        ax.figure.patch.set_facecolor(self.DARK_BG)
        ax.set_title(title, fontsize=10, fontweight="bold", color="white")
        ax.tick_params(colors="white", labelsize=8)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        for s in ax.spines.values():
            s.set_color(self.SPINE)

    # Отрисовка круговой диаграммы
    def _draw_defect_types(self, engine):
        fig = self.fig_pie
        fig.clear()
        ax = fig.add_subplot(111)

        data = engine.get_defect_types_chart_data()
        if not data.empty:
            if len(data) > 5:
                head = data.head(5)
                others = pd.Series([data.iloc[5:].sum()], index=["Другие"])
                plot_data = pd.concat([head, others])
            else:
                plot_data = data

            ax.pie(
                plot_data, labels=plot_data.index, autopct="%1.0f%%",
                startangle=140, textprops={"fontsize": 8, "color": "white"},
            )
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", color="white")

        self._theme(ax, "Типы дефектов")
        fig.tight_layout()

    # Отрисовка гистограммы распределения глубин дефектов
    def _draw_depth_hist(self, engine):
        fig = self.fig_bar
        fig.clear()
        ax = fig.add_subplot(111)

        depths = engine.get_depth_histogram_data()
        if depths:
            ax.hist(depths, bins=20, color="#F44336", edgecolor="#1e1e1e")
            ax.set_xlabel("Глубина, %", fontsize=8)
            ax.set_ylabel("Кол-во", fontsize=8)
            ax.grid(axis="y", alpha=0.2, color="white")
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", color="white")

        self._theme(ax, "Распределение глубин")
        fig.tight_layout()

    # Отрисовка столбчатой диаграмы труб с наибольшим количеством дефектов
    def _draw_top_pipes(self, current_df: pd.DataFrame):
        fig = self.fig_top
        fig.clear()
        ax = fig.add_subplot(111)

        valid = current_df.dropna(subset=["Номер трубы", "Регион"]) if not current_df.empty else None
        if valid is not None and not valid.empty:
            counts = (
                valid.groupby(["Регион", "Номер трубы"])
                .size().reset_index(name="count")
            )
            top10 = (
                counts.sort_values(by="count", ascending=False)
                .head(10).sort_values(by="count", ascending=True)
            )
            labels = [str(r["Номер трубы"]) for _, r in top10.iterrows()]
            colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(top10)))
            bars = ax.barh(labels, top10["count"], color=colors, edgecolor="#1e1e1e")
            ax.set_xlabel("Кол-во дефектов", fontsize=8)
            for bar in bars:
                w = bar.get_width()
                ax.text(w, bar.get_y() + bar.get_height() / 2, f" {int(w)}",
                        va="center", ha="left", fontsize=7, color="white")
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", color="white")

        self._theme(ax, "Топ-10 проблемных труб")
        fig.subplots_adjust(left=0.15, right=0.95, top=0.85, bottom=0.15)

# Главное окно, объединяющее все элементы дашборда
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

    # Создание главного контейнера
    def _init_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: #1e1e1e;")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.addWidget(self._build_filters())
        root.addLayout(self._build_kpi_row())
        root.addWidget(self._build_splitter())

    # Создание панели фильтрации
    def _build_filters(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { background-color: #333333; border-radius: 5px; padding: 5px; }
            QLabel { font-weight: bold; color: white; }
            QComboBox { background-color: white; color: black; padding: 3px; }
        """)
        lay = QHBoxLayout(panel)

        lay.addWidget(QLabel("Участок (Регион):"))
        self.combo_region = QComboBox()
        self.combo_region.setMinimumWidth(200)
        self.combo_region.currentIndexChanged.connect(self._on_region_changed)
        lay.addWidget(self.combo_region)

        lay.addWidget(QLabel("Год:"))
        self.combo_year = QComboBox()
        lay.addWidget(self.combo_year)

        lay.addWidget(QLabel("Расположение:"))
        self.combo_loc = QComboBox()
        lay.addWidget(self.combo_loc)

        lay.addWidget(QLabel("Опасность:"))
        self.combo_haz = QComboBox()
        lay.addWidget(self.combo_haz)

        lay.addStretch()

        self.btn_apply = QPushButton("Применить фильтры")
        self.btn_apply.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold;
                          padding: 5px 15px; border-radius: 3px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_apply.clicked.connect(self.update_dashboard)
        lay.addWidget(self.btn_apply)

        return panel

    # Создание панели ключевых показателей
    def _build_kpi_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.kpi_total = KpiCard("Всего", "#2196F3")
        self.kpi_avg = KpiCard("Средняя глубина", "#FF9800")
        self.kpi_max = KpiCard("Макс. глубина", "#F44336")
        self.kpi_unique = KpiCard("Уникальных дефектов", "#9C27B0")
        for card in (self.kpi_total, self.kpi_avg, self.kpi_max, self.kpi_unique):
            row.addWidget(card)
        return row

    # Создание разделителя для изменения размера графиков
    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._build_charts())
        splitter.addWidget(self._build_table())
        splitter.setSizes([400, 300])
        return splitter

    # Создание панели с графиками
    def _build_charts(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)

        self.fig_pie = Figure(figsize=(4, 3), dpi=100)
        self.canvas_pie = FigureCanvas(self.fig_pie)
        lay.addWidget(self.canvas_pie)

        self.fig_bar = Figure(figsize=(4, 3), dpi=100)
        self.canvas_bar = FigureCanvas(self.fig_bar)
        lay.addWidget(self.canvas_bar)

        self.fig_top = Figure(figsize=(4, 3), dpi=100)
        self.canvas_top = FigureCanvas(self.fig_top)
        lay.addWidget(self.canvas_top)

        self.chart_renderer = ChartRenderer(self.fig_pie, self.fig_bar, self.fig_top)
        return w

    # Создание панели таблицы и применяет стили к таблицы
    def _build_table(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)

        lbl = QLabel("10 самых опасных дефектов (отсортировано по глубине):")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        lay.addWidget(lbl)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.setStyleSheet("""
            QTableView {
                background-color: #2b2b2b;
                alternate-background-color: #333333;
                color: #e0e0e0;
                selection-background-color: #0078D7;
                selection-color: white;
                border: 1px solid #444444;
                border-radius: 8px;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: #1e1e1e; color: #ffffff; font-weight: bold;
                padding: 6px; border: none;
                border-bottom: 2px solid #0078D7;
                border-right: 1px solid #444444;
            }
            QHeaderView::section:last { border-right: none; }
            QTableCornerButton::section { background-color: #1e1e1e; border: none; }
        """)
        lay.addWidget(self.table)
        return w

    # Заполняет список регионов
    def _load_initial_filters(self):
        regions = sorted(self.full_df["Регион"].dropna().unique())
        self.combo_region.blockSignals(True)
        self.combo_region.clear()
        self.combo_region.addItems(regions)
        self.combo_region.blockSignals(False)

        self._on_region_changed()
        self.update_dashboard()

    # Обновляет список доступных годов при смене региона
    def _on_region_changed(self):
        region = self.combo_region.currentText()
        df_region = self.full_df[self.full_df["Регион"] == region]
        years = sorted(str(int(y)) for y in df_region["Год обследования"].dropna().unique())

        self.combo_year.blockSignals(True)
        self.combo_year.clear()
        self.combo_year.addItems(years)
        self.combo_year.blockSignals(False)

        self._update_other_filters(df_region)

    # Обновляет списки расположения и опастности на основе региона
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

    # Обновляет данные в дашборде
    def update_dashboard(self):
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

        self.engine = AnalyticsEngine(df_geo)
        self.current_df = self.engine.filter_data(filters)
        self.engine.df = self.current_df

        self._refresh_kpi()
        self.chart_renderer.redraw_all(self.engine, self.current_df)
        self.canvas_pie.draw()
        self.canvas_bar.draw()
        self.canvas_top.draw()
        self._refresh_table()

    # Вставка значений в карточки ключевых показателей
    def _refresh_kpi(self):
        k = self.engine.get_kpis()
        self.kpi_total.set_value(k["total"])
        self.kpi_avg.set_value(f"{k['avg_depth']} %")
        self.kpi_max.set_value(f"{k['max_depth']} %")
        self.kpi_unique.set_value(k["unique_defects"])

    # Формирование таблицы
    def _refresh_table(self):
        if self.current_df.empty:
            self.table.setModel(PandasModel(pd.DataFrame(columns=["Нет данных"])))
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
