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
            return {"total": 0, "pipes_replacement": 0, "max_depth": 0.0, "unique_defects": 0}

        total = len(self.df)

        max_depth = float(self.df["Глубина, %"].max())

        unique_defects = self.df["Характер особенности"].nunique()

        if "Опасность" in self.df.columns and "Номер трубы" in self.df.columns:
            pipes_replacement = self.df[self.df["Опасность"] == "(a)"]["Номер трубы"].nunique()
        else:
            pipes_replacement = 0

        return {
            "total": total,
            "pipes_replacement": pipes_replacement,
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
    def get_table_data(self, mode: int) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame()

        if mode == 0:
            display = self.df.sort_values(by="Глубина, %", ascending=False, na_position="last")
            visible_cols = [
                "Номер трубы", "Расстояние, м", "Глубина, %",
                "Характер особенности", "Расположение", "Опасность",
            ]
            visible_cols = [c for c in visible_cols if c in display.columns]
            other_cols = [c for c in display.columns if c not in visible_cols]
            return display[visible_cols + other_cols].reset_index(drop=True)

        else:
            valid = self.df.dropna(subset=["Номер трубы"])
            if valid.empty:
                return pd.DataFrame()

            grouped = valid.groupby("Номер трубы").agg(
                total=("Номер трубы", "size"),
                count_a=("Опасность", lambda x: (x == "(a)").sum()),
                count_b=("Опасность", lambda x: (x == "(b)").sum()),
                count_c=("Опасность", lambda x: (x == "(c)").sum()),
            ).reset_index()

            grouped.rename(columns={
                "total": "Кол-во дефектов",
                "count_a": "Класс (a)",
                "count_b": "Класс (b)",
                "count_c": "Класс (c)"
            }, inplace=True)

            grouped["_priority"] = grouped.apply(
                lambda r: 3 if r["Класс (a)"] > 0 else (2 if r["Класс (b)"] > 0 else (1 if r["Класс (c)"] > 0 else 0)),
                axis=1
            )

            # Сортировка: сначала по приоритету, затем по общему числу дефектов
            grouped = grouped.sort_values(by=["_priority", "Кол-во дефектов"], ascending=[False, False])
            return grouped.drop(columns=["_priority"]).reset_index(drop=True)

    # Получение общей информации по конкретной трубе
    def get_pipe_details(self, pipe_number: str) -> dict:
        pipe_df = self.df[self.df["Номер трубы"].astype(str) == str(pipe_number)]
        if pipe_df.empty:
            return {}

        first_row = pipe_df.iloc[0]

        details = {
            "Номер трубы": str(pipe_number),
            "Регион": first_row.get("Регион", "Нет данных"),
            "Год обследования": first_row.get("Год обследования"),
            "Всего дефектов": len(pipe_df),
            "Макс. глубина, %": pipe_df["Глубина, %"].max(),
            "Класс (a)": len(pipe_df[pipe_df["Опасность"] == "(a)"]),
            "Класс (b)": len(pipe_df[pipe_df["Опасность"] == "(b)"]),
            "Класс (c)": len(pipe_df[pipe_df["Опасность"] == "(c)"]),
        }

        if "Длина трубы, м" in pipe_df.columns:
            details["Длина трубы, м"] = first_row["Длина трубы, м"]
        if "Толщина, мм" in pipe_df.columns:
            details["Толщина, мм"] = first_row["Толщина, мм"]

        for k, v in details.items():
            if pd.isna(v):
                details[k] = "Нет данных"
            elif isinstance(v, float):
                if k == "Год обследования":
                    details[k] = str(int(v))
                else:
                    details[k] = round(v, 2)

        return details
