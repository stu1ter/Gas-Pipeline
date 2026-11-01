from numbers import Real
from pathlib import Path
from typing import ClassVar

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QColor


class DataLoader:
    # Обязательные столбцы нового набора данных
    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "Номер трубы",
        "Расстояние, м_аном",
        "Глубина, %",
        "Регион",
        "Год обследования",
        "Характер особенности",
    ]

    # Столбцы, которые должны иметь числовой тип
    NUMERIC_COLUMNS: ClassVar[list[str]] = [
        "Расстояние, м_аном",
        "Расстояние, м_швы",
        "Расстояние, м",
        "Длина трубы, м",
        "Толщина, мм",
        "Глубина, %",
        "Год обследования",
        "Ориентация центра, sin",
        "Ориентация центра, cos",
        "Широта",
        "Долгота",
        "Высота, м",
    ]

    # Загружает CSV-файл, проверяет обязательные столбцы и выполняет очистку данных.
    def load_and_clean(self, filepath: str) -> pd.DataFrame:
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {filepath}")

        try:
            df = pd.read_csv(
                path,
                encoding="utf-8-sig",
                dtype=str,
                keep_default_na=False,
            )
        except UnicodeDecodeError:
            df = pd.read_csv(
                path,
                encoding="cp1251",
                dtype=str,
                keep_default_na=False,
            )

        # Убирает пробелы и замены пустоты на NaN
        df.columns = [str(col).strip() for col in df.columns]
        df = df.replace(r"^\s*$", pd.NA, regex=True)

        # Проверяем наличие обязательных столбцов
        missing = [
            col for col in self.REQUIRED_COLUMNS
            if col not in df.columns
        ]

        if missing:
            raise ValueError(
                "Отсутствуют обязательные столбцы: "
                + ", ".join(missing)
            )

        return self._clean(df)

    # Очищает и приводит данные к форматам, необходимым для аналитики и отображения.
    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if "Расстояние, м_аном" in df.columns:
            df = df.rename(
                columns={
                    "Расстояние, м_аном": "Расстояние, м"
                }
            )

        # Удаляем лишние пробелы в текстовых столбцах
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].apply(
                lambda value: value.strip()
                if isinstance(value, str)
                else value
            )

        # Приводим числовые столбцы к числовому типу
        for col in self.NUMERIC_COLUMNS:
            if col in df.columns:
                values = (
                    df[col]
                    .astype("string")
                    .str.replace(",", ".", regex=False)
                    .str.strip()
                )

                df[col] = pd.to_numeric(
                    values,
                    errors="coerce",
                )

        if "Глубина, %" in df.columns:
            df.loc[
                df["Глубина, %"] < 0,
                "Глубина, %"
            ] = pd.NA

        for col in ["Расстояние, м", "Расстояние, м_швы"]:
            if col in df.columns:
                df.loc[df[col] < 0, col] = pd.NA

        # Очистка идентификаторов труб
        if "Номер трубы" in df.columns:
            pipe = (
                df["Номер трубы"]
                .astype("string")
                .str.strip()
            )

            missing_pipe = pipe.str.casefold().isin(
                ["", "nan", "none", "<na>", "null"]
            )

            df["Номер трубы"] = pipe
            df.loc[missing_pipe, "Номер трубы"] = pd.NA

        # Очистка значений опасности
        if "Опасность" in df.columns:
            danger = (
                df["Опасность"]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            valid_values = ["(a)", "(b)", "(c)"]

            df["Опасность"] = danger
            df.loc[
                ~df["Опасность"].isin(valid_values),
                "Опасность"
            ] = pd.NA

        return df

# Модель pandas DataFrame для отображения данныx в таблице PyQt6.
class PandasModel(QAbstractTableModel):
    def __init__(self, data: pd.DataFrame):
        super().__init__()

        self._data = data
        self._headers = list(data.columns)

        self._cache_display = []
        self._cache_fg = []
        self._cache_bg = []

        self._build_cache()

    # Форматирует значение для отображения в таблице
    @staticmethod
    def _format_value(col, val):
        if pd.isna(val):
            return ""

        if isinstance(val, Real) and not isinstance(val, bool):
            if col == "Год обследования":
                return str(int(float(val)))

            if col == "Глубина, %":
                return f"{val:.1f}"

            return f"{val:.2f}"

        return str(val)

    #Предварительно формирует отображаемые значения и цвета ячеек для ускорения работы таблицы.
    def _build_cache(self):
        self._cache_display.clear()
        self._cache_fg.clear()
        self._cache_bg.clear()

        for _, row in self._data.iterrows():
            row_display = []
            row_foreground = []
            row_background = []

            for col, val in row.items():

                # Форматирование значения
                row_display.append(
                    self._format_value(col, val)
                )

                # Цвет текста
                fg = None

                if col == "Опасность":
                    if val == "(a)":
                        fg = QColor("#FF5252")
                    elif val == "(b)":
                        fg = QColor("#FFA726")
                    elif val == "(c)":
                        fg = QColor("#FFEB3B")

                elif (
                    col == "Глубина, %"
                    and pd.notna(val)
                    and val >= 40.0
                ):
                    fg = QColor("#FF5252")

                row_foreground.append(fg)

                # Цвет фона
                bg = None

                if col == "Опасность" and val == "(a)":
                    bg = QColor(255, 82, 82, 40)

                row_background.append(bg)

            self._cache_display.append(row_display)
            self._cache_fg.append(row_foreground)
            self._cache_bg.append(row_background)

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0

        return len(self._cache_display)

    def columnCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0

        return len(self._headers)

    # Выдает текст, цвета и данные для сортировки по запросу.
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if (
            row < 0
            or row >= len(self._cache_display)
            or col < 0
            or col >= len(self._headers)
        ):
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return self._cache_display[row][col]

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignCenter)

        if role == Qt.ItemDataRole.ForegroundRole:
            return self._cache_fg[row][col]

        if role == Qt.ItemDataRole.BackgroundRole:
            return self._cache_bg[row][col]

        if role == Qt.ItemDataRole.UserRole:
            val = self._data.iloc[row, col]

            if pd.isna(val):
                return ""

            if isinstance(val, Real) and not isinstance(val, bool):
                return float(val)

            return str(val).lower()

        return None

    # Отрисовка заголовков таблиц
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._headers):
                return self._headers[section]

            elif orientation == Qt.Orientation.Vertical and 0 <= section < len(self._data.index):
                return str(self._data.index[section])

        return None

    #  Возвращает данные выбранной строки в виде словаря для карточки аномалии.
    def get_row_dict(self, row: int) -> dict:
        if row < 0 or row >= len(self._data):
            return {}

        row_data = self._data.iloc[row]
        result = {}

        for col, val in row_data.items():

            if pd.isna(val):
                result[col] = "Нет данных"
            else:
                result[col] = self._format_value(col, val)

        return result
