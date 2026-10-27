# Отрисовка трёх графиков дашборда.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from .theme import Palette


class ChartRenderer:
    DARK_BG = Palette.PANEL
    SPINE = Palette.BORDER

    def __init__(self, fig_pie: Figure, fig_bar: Figure, fig_top: Figure):
        self.fig_pie = fig_pie
        self.fig_bar = fig_bar
        self.fig_top = fig_top

    def redraw_all(self, engine, current_df: pd.DataFrame):
        self._draw_defect_types(engine)
        self._draw_depth_hist(engine)
        self._draw_top_pipes(current_df)

    # -- внутреннее -----------------------------------------------------
    def _theme(self, ax, title):
        ax.set_facecolor(self.DARK_BG)
        ax.figure.patch.set_facecolor(self.DARK_BG)
        ax.set_title(title, fontsize=10, fontweight="bold", color=Palette.TEXT)
        ax.tick_params(colors=Palette.TEXT_DIM, labelsize=8)
        ax.xaxis.label.set_color(Palette.TEXT_DIM)
        ax.yaxis.label.set_color(Palette.TEXT_DIM)
        for s in ax.spines.values():
            s.set_color(self.SPINE)

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
                startangle=140,
                textprops={"fontsize": 8, "color": Palette.TEXT},
                wedgeprops={"edgecolor": Palette.BG, "linewidth": 1},
            )
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    color=Palette.TEXT_DIM)

        self._theme(ax, "Типы дефектов")

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

    def _draw_top_pipes(self, current_df: pd.DataFrame):
        fig = self.fig_top
        fig.clear()
        ax = fig.add_subplot(111)

        valid = (
            current_df.dropna(subset=["Номер трубы", "Регион"])
            if not current_df.empty else None
        )
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
            colors = plt.cm.Blues(np.linspace(0.45, 0.85, len(top10)))
            bars = ax.barh(labels, top10["count"], color=colors,
                           edgecolor=Palette.BG)
            ax.set_xlabel("Кол-во дефектов", fontsize=8)
            for bar in bars:
                w = bar.get_width()
                ax.text(w, bar.get_y() + bar.get_height() / 2, f" {int(w)}",
                        va="center", ha="left", fontsize=7,
                        color=Palette.TEXT)
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    color=Palette.TEXT_DIM)

        self._theme(ax, "Топ-10 проблемных труб")
