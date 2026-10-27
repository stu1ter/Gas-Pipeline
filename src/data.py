# Загрузка, очистка данных и Qt-модель для таблицы
import re
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QColor


# Загружает CSV и приводит его к пригодному виду
class DataLoader:
    REQUIRED_COLUMNS = [
        "Номер трубы", "Расстояние, м", "Глубина, %",
        "Ориентация центра, ч:мин", "Регион", "Год обследования",
        "Характер особенности",
    ]

    # Метод загрузки, провекри REQUIRED_COLUMNS и запуска _clean
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

    # Метод удаления некорректных значений и отчистки типов данных
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

    # Исправление некорректоного времени
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

# Позволяет отображать DataFrame в таблице в PyQt
class PandasModel(QAbstractTableModel):
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    # Возвращяет данные и стиль для каждой ячейки
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        val = self._data.iloc[index.row(), index.column()]
        col_name = self._data.columns[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            if pd.isna(val):
                return ""
            if isinstance(val, float):
                return f"{val:.2f}"
            return str(val)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignCenter)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col_name == "Опасность":
                if val == "(a)":
                    return QColor("#FF5252")
                if val == "(b)":
                    return QColor("#FFA726")
                if val == "(c)":
                    return QColor("#FFEB3B")
            if col_name == "Глубина, %" and pd.notna(val) and val >= 40.0:
                return QColor("#FF5252")

        if role == Qt.ItemDataRole.BackgroundRole:
            if col_name == "Опасность" and val == "(a)":
                return QColor(255, 82, 82, 40)

        return None

    # Задает названия колонок и нумерацию строк
    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None
