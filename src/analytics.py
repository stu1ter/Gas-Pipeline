# type: ignore
from typing import ClassVar

import pandas as pd


# Расчет ключевых показателей, подготовка данных для графиков и таблицы
class AnalyticsEngine:

    LOC_MAP: ClassVar[dict[str, str]] = {
        "EXT": "Внешний (EXT)",
        "INT": "Внутренний (INT)",
        "MID": "В теле металла (MID)",
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    # Фильтрация данных
    def filter_data(self, filters: dict) -> pd.DataFrame:
        filtered_df = self.df.copy()
        for col, val in filters.items():
            if col in filtered_df.columns and val and val != "Все":
                filtered_df = filtered_df[filtered_df[col] == val]
        return filtered_df

    # Вычисление ключевых показателей
    def get_kpis(self) -> dict:
        if self.df.empty:
            return {"total": 0, "avg_depth": 0.0, "max_depth": 0.0, "unique_defects": 0}

        total = len(self.df)

        avg_depth = float(self.df["Глубина, %"].mean())
        max_depth = float(self.df["Глубина, %"].max())

        unique_defects = self.df["Характер особенности"].nunique()

        return {
            "total": total,
            "avg_depth": round(avg_depth, 1) if pd.notna(avg_depth) else 0.0,
            "max_depth": round(max_depth, 1) if pd.notna(max_depth) else 0.0,
            "unique_defects": unique_defects
        }

    # Подготовка данных для круговой диаграммы
    def get_defect_types_chart_data(self) -> pd.Series:
        if self.df.empty:
            return pd.Series(dtype=int)

        counts = self.df["Характер особенности"].value_counts()
        return counts

    # Подготовка данных для гистограммы
    def get_depth_histogram_data(self) -> list:
        return self.df["Глубина, %"].dropna().tolist()

    # Подготовка данных для графика труб с наибольшим количеством дефектов
    def get_top_pipes_grouped(self, top_n: int = 10) -> pd.DataFrame:
        cols = ["Регион", "Номер трубы", "count"]
        if self.df.empty:
            return pd.DataFrame(columns=cols)

        if "Номер трубы" not in self.df.columns or "Регион" not in self.df.columns:
            return pd.DataFrame(columns=cols)

        valid = self.df.dropna(subset=["Номер трубы", "Регион"])
        if valid.empty:
            return pd.DataFrame(columns=cols)

        counts = (
            valid.groupby(["Регион", "Номер трубы"])
            .size()
            .reset_index(name="count")
        )

        top_n_df = (
            counts.sort_values(by="count", ascending=False)
            .head(top_n)
            .sort_values(by="count", ascending=True)
            .reset_index(drop=True)
        )
        return top_n_df

    # Подготовка данных для таблицы
    def get_table_data(self, mode: int, top_n: int = 10) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame()

        base_df = self.df.sort_values(by="Глубина, %", ascending=False, na_position="last")

        if mode == 0:
            display = base_df.copy()
        else:
            valid = base_df.dropna(subset=["Глубина, %"])
            if valid.empty:
                return pd.DataFrame()
            display = valid.head(top_n).copy()

        visible_cols = [
            "Номер трубы", "Расстояние, м", "Глубина, %",
            "Характер особенности", "Расположение", "Опасность",
        ]
        visible_cols = [c for c in visible_cols if c in display.columns]
        other_cols = [c for c in display.columns if c not in visible_cols]

        return display[visible_cols + other_cols].reset_index(drop=True)
