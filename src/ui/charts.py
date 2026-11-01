# ui/charts.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget

from .theme import Palette


class ChartRenderer:
    DARK_BG = Palette.PANEL
    SPINE = Palette.BORDER

    def __init__(self):
        self.fig_pie = Figure(figsize=(4, 3), dpi=100, constrained_layout=True)
        self.canvas_pie = FigureCanvas(self.fig_pie)

        self.fig_bar = Figure(figsize=(4, 3), dpi=100, constrained_layout=True)
        self.canvas_bar = FigureCanvas(self.fig_bar)

        self.fig_top = Figure(figsize=(4, 3), dpi=100, constrained_layout=True)
        self.canvas_top = FigureCanvas(self.fig_top)

    # Возвращает список виджетов для вставки в интерфейс
    def get_canvases(self) -> list[QWidget]:
        return [self.canvas_pie, self.canvas_bar, self.canvas_top]

    # Перерисовывает все графики на основе новых данных
    def redraw_all(self, engine, current_df: pd.DataFrame):
        self._draw_defect_types(engine)
        self._draw_depth_hist(engine)
        self._draw_top_pipes(engine)

        # Обновляем отрисовку канвасов
        self.canvas_pie.draw_idle()
        self.canvas_bar.draw_idle()
        self.canvas_top.draw_idle()

    # Единый дизайн графиков
    def _theme(self, ax, title):
        ax.set_facecolor(self.DARK_BG)
        ax.figure.patch.set_facecolor(self.DARK_BG)
        ax.set_title(title, fontsize=10, fontweight="bold", color=Palette.TEXT)
        ax.tick_params(colors=Palette.TEXT_DIM, labelsize=8)
        ax.xaxis.label.set_color(Palette.TEXT_DIM)
        ax.yaxis.label.set_color(Palette.TEXT_DIM)
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
                plot_data, labels=[str(x) for x in plot_data.index], autopct="%1.0f%%",
                startangle=140,
                textprops={"fontsize": 8, "color": Palette.TEXT},
                wedgeprops={"edgecolor": Palette.BG, "linewidth": 1},
            )
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    color=Palette.TEXT_DIM)

        self._theme(ax, "Типы дефектов")

    # Отрисовка гистрограммы
    def _draw_depth_hist(self, engine):
        fig = self.fig_bar
        fig.clear()
        ax = fig.add_subplot(111)

        depths = engine.get_depth_histogram_data()
        if depths:
            ax.hist(depths, bins=20, color=Palette.KPI_RED,
                    edgecolor=Palette.BG)
            ax.set_xlabel("Глубина, %", fontsize=8)
            ax.set_ylabel("Кол-во", fontsize=8)
            ax.grid(axis="y", alpha=0.15, color=Palette.TEXT)
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    color=Palette.TEXT_DIM)

        self._theme(ax, "Распределение глубин")

    # Отрисовка бар-чарта
    def _draw_top_pipes(self, engine):
        fig = self.fig_top
        fig.clear()
        ax = fig.add_subplot(111)

        top_n_df = engine.get_top_pipes_grouped()

        if not top_n_df.empty:
            labels = top_n_df["Номер трубы"].astype(str).tolist()
            values = top_n_df["count"].tolist()
            colors = plt.cm.Blues(np.linspace(0.45, 0.85, len(top_n_df)))
            bars = ax.barh(labels, values, color=colors, edgecolor=Palette.BG)
            ax.set_xlabel("Кол-во дефектов", fontsize=8)
            for bar in bars:
                w = bar.get_width()
                ax.text(w, bar.get_y() + bar.get_height() / 2, f" {int(w)}",
                        va="center", ha="left", fontsize=7, color=Palette.TEXT)
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    color=Palette.TEXT_DIM)

        self._theme(ax, "Топ-10 проблемных труб")
