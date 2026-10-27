# Загрузка, очистка данных и Qt-модель для таблицы
import re
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QColor


class DataLoader:
    REQUIRED_COLUMNS = [
        "Номер трубы", "Расстояние, м", "Глубина, %",
        "Ориентация центра, ч:мин", "Регион", "Год обследования",
        "Характер особенности",
    ]

    def load_and_clean(self, filepath: str) -> pd.DataFrame:
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Файл не найден: {filepath}")

        df = (
            pd.read_csv(filepath, encoding="utf-8-sig", dtype=str, keep_default_na=False)
            .replace("", pd.NA)
        )
        df.columns = [c.strip() for c in df.columns]

        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Отсутствуют обязательные столбцы: {', '.join(missing)}")

        return self._clean(df)

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in [c for c in df.columns if "ч:мин" in c]:
            df[col] = df[col].apply(self._fix_time)

        for col in ["Расстояние, м", "Длина трубы, м", "Толщина, мм",
                    "Глубина, %", "Год обследования"]:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(",", ".", regex=False),
                    errors="coerce",
                )

        if "Глубина, %" in df.columns:
            df.loc[df["Глубина, %"] < 0, "Глубина, %"] = pd.NA

        if "Номер трубы" in df.columns:
            df["Номер трубы"] = df["Номер трубы"].astype(str).str.strip()
            df.loc[df["Номер трубы"] == "nan", "Номер трубы"] = pd.NA

        if "Опасность" in df.columns:
            df["Опасность"] = df["Опасность"].astype(str).str.strip()
            valid = ["(a)", "(b)", "(c)"]
            df.loc[~df["Опасность"].isin(valid), "Опасность"] = pd.NA

        return df

    @staticmethod
    def _fix_time(val):
        if pd.isna(val) or not isinstance(val, str):
            return val
        match = re.match(r"^(\d{1,2}):(\d{2})$", val.strip())
        if not match:
            return val
        h, m = int(match.group(1)), int(match.group(2))
        if m >= 60:
            h += m // 60
            m %= 60
        return f"{h:02d}:{m:02d}"


class PandasModel(QAbstractTableModel):
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data
        self._headers = list(data.columns)
        self._cache_display = []
        self._cache_fg = []
        self._cache_bg = []
        self._build_cache()

    def _build_cache(self):
        """Предрасчет отображаемых строк и цветов для мгновенной отрисовки."""
        self._cache_display.clear()
        self._cache_fg.clear()
        self._cache_bg.clear()

        for _, row in self._data.iterrows():
            row_disp = []
            row_fg = []
            row_bg = []
            for col, val in row.items():
                # 1. Отображение
                if pd.isna(val):
                    row_disp.append("")
                elif isinstance(val, float):
                    row_disp.append(f"{val:.2f}")
                else:
                    row_disp.append(str(val))

                # 2. Цвет текста (Foreground)
                fg = None
                if col == "Опасность":
                    if val == "(a)": fg = QColor("#FF5252")
                    elif val == "(b)": fg = QColor("#FFA726")
                    elif val == "(c)": fg = QColor("#FFEB3B")
                elif col == "Глубина, %" and pd.notna(val) and val >= 40.0:
                    fg = QColor("#FF5252")
                row_fg.append(fg)

                # 3. Цвет фона (Background)
                bg = None
                if col == "Опасность" and val == "(a)":
                    bg = QColor(255, 82, 82, 40)
                row_bg.append(bg)

            self._cache_display.append(row_disp)
            self._cache_fg.append(row_fg)
            self._cache_bg.append(row_bg)

    def rowCount(self, parent=None):
        return len(self._cache_display)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        r, c = index.row(), index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._cache_display[r][c]

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignCenter)

        if role == Qt.ItemDataRole.ForegroundRole:
            return self._cache_fg[r][c]

        if role == Qt.ItemDataRole.BackgroundRole:
            return self._cache_bg[r][c]

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None

    def sort(self, column, order):
        """Встроенная сортировка."""
        col_name = self._headers[column]
        self.layoutAboutToBeChanged.emit()

        self._data = self._data.sort_values(
            by=col_name,
            ascending=(order == Qt.SortOrder.AscendingOrder),
            na_position="last",
        ).reset_index(drop=True)

        self._build_cache() # Пересчитываем кэш после сортировки
        self.layoutChanged.emit()

    def get_row_dict(self, row: int) -> dict:
        if row < 0 or row >= self.rowCount():
            return {}

        row_data = self._data.iloc[row]
        result = {}
        for col, val in row_data.items():
            if pd.isna(val):
                result[col] = "Нет данных"
            elif isinstance(val, float):
                result[col] = f"{val:.2f}"
            else:
                result[col] = str(val)
        return result
