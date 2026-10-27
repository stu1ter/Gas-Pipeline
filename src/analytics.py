import pandas as pd


# Расчет ключевых показателей, подготовка данных для графиков и таблицы
class AnalyticsEngine:
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

        avg_depth = self.df["Глубина, %"].mean()
        max_depth = self.df["Глубина, %"].max()

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
    def get_top_pipes_data(self, top_n: int = 10) -> pd.Series:
        if self.df.empty or "Номер трубы" not in self.df.columns:
            return pd.Series(dtype=int)

        pipe_counts = self.df["Номер трубы"].value_counts().head(top_n)
        return pipe_counts

    # Подготовка данных для таблицы труб самых опасных дефектов
    def get_top_defects_table(self, top_n: int = 10) -> pd.DataFrame:
        if self.df.empty or "Глубина, %" not in self.df.columns:
            return pd.DataFrame()

        cols_to_show = ["Номер трубы", "Расстояние, м", "Глубина, %", "Характер особенности", "Расположение", "Опасность"]
        cols_to_show = [c for c in cols_to_show if c in self.df.columns]

        top_df = self.df.dropna(subset=["Глубина, %"]).sort_values(by="Глубина, %", ascending=False).head(top_n)

        return top_df[cols_to_show]
