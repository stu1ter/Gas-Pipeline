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
        self._draw_danger_classes(engine)
        self._draw_distance_concentration(engine)

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

    # Отрисовка горизонтальной диаграммы классов опасности
    def _draw_danger_classes(self, engine):
        fig = self.fig_bar
        fig.clear()
        ax = fig.add_subplot(111)

        data = engine.get_danger_classes_data()

        labels = []
        values = []
        colors = []

        class_info = [
            ("(a)", data["(a)"], "#FF5252"),
            ("(b)", data["(b)"], "#FFA726"),
            ("(c)", data["(c)"], "#FFEB3B"),
        ]

        for label, val, color in class_info:
            if val > 0:
                labels.append(label)
                values.append(val)
                colors.append(color)

        if values:
            bars = ax.barh(labels, values, color=colors, edgecolor=Palette.BG, height=0.6)
            ax.invert_yaxis()

            for bar in bars:
                w = bar.get_width()
                ax.text(w + max(values)*0.02, bar.get_y() + bar.get_height() / 2,
                        f"{int(w)}", va="center", ha="left", fontsize=9,
                        color=Palette.TEXT, fontweight="bold")


            ax.set_xlim(0, max(values) * 1.15)
            ax.set_xlabel("Кол-во дефектов", fontsize=8)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            ax.grid(axis="x", alpha=0.15, color=Palette.TEXT)
            ax.set_axisbelow(True)
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", color=Palette.TEXT_DIM)
            ax.set_yticks([])

        self._theme(ax, "Распределение по классам")

    def _draw_distance_concentration(self, engine):
        fig = self.fig_top
        fig.clear()
        ax = fig.add_subplot(111)

        distances = engine.get_distance_chart_data()

        if distances:
            ax.hist(distances, bins=30, color=Palette.KPI_PURPLE, edgecolor=Palette.BG)
            ax.set_xlabel("Расстояние, м", fontsize=8)
            ax.set_ylabel("Кол-во дефектов", fontsize=8)
            ax.grid(axis="y", alpha=0.15, color=Palette.TEXT)
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    color=Palette.TEXT_DIM)

        self._theme(ax, "Концентрация по расстоянию")
