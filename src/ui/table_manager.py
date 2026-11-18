from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import QTabBar, QTabWidget, QVBoxLayout, QWidget

from analytics import AnalyticsEngine
from data import PandasModel
from ui.widgets import DataTable, TabCloseButton


# Управляет вкладками, таблицами и их моделями данных
class TableManager:
    def __init__(self, tab_widget: QTabWidget, detail_card):
        self.tabs = tab_widget
        self.detail_card = detail_card
        self.engine = None

        self.table_all = DataTable()
        self.table_summary = DataTable()

        self.proxy_all = None
        self.proxy_summary = None

        self.custom_tables = []

    # Создает базовые вкладки и скрывает у них крестики
    def setup_base_tabs(self):
        tab_all_widget, self.table_all = self._create_table_widget()
        self.tabs.addTab(tab_all_widget, "Все аномалии")

        tab_summary_widget, self.table_summary = self._create_table_widget()
        self.tabs.addTab(tab_summary_widget, "Сводка по трубам")

        for i in range(2):
            self.tabs.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)

    # Создает контейнер с таблицей
    def _create_table_widget(self) -> tuple[QWidget, DataTable]:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        table = DataTable()
        lay.addWidget(table)
        return container, table

    # Обновляет данные во всех базовых таблицах
    def update_tables(self, engine: AnalyticsEngine):
        self.engine = engine
        self._setup_base_table(0, self.table_all, 'proxy_all', 'source_all')
        self._setup_base_table(1, self.table_summary, 'proxy_summary', 'source_summary')

    # Настраивает конкретную базовую таблицу
    def _setup_base_table(self, mode: int, table: DataTable, proxy_attr: str, source_attr: str):
        display = self.engine.get_table_data(mode=mode)
        visible_cols_count = 6 if mode == 0 else 5

        if display.empty:
            table.setModel(PandasModel(display))
            setattr(self, proxy_attr, None)
            return

        source_model = PandasModel(display)
        proxy_model = QSortFilterProxyModel(self.tabs)
        proxy_model.setSourceModel(source_model)
        proxy_model.setSortRole(Qt.ItemDataRole.UserRole)

        table.setModel(proxy_model)
        setattr(self, proxy_attr, proxy_model)
        setattr(self, source_attr, source_model)

        for i in range(len(display.columns)):
            table.setColumnHidden(i, i >= visible_cols_count)

        table.resizeColumnsToContents()

        header = table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(header.ResizeMode.Stretch)

        try:
            table.selectionModel().selectionChanged.disconnect()
        except TypeError:
            pass

        table.selectionModel().selectionChanged.connect(
            lambda sel, des, p=proxy_model, m=mode: self._on_row_selected(sel, p, m)
        )

        if proxy_model.rowCount() > 0:
            table.selectRow(0)
        else:
            self.detail_card.clear()

    # Обработчик выбора строки в базовой таблице
    def _on_row_selected(self, selected, proxy_model, mode: int):
        indexes = selected.indexes()
        if not indexes:
            self.detail_card.clear()
            return

        source_index = proxy_model.mapToSource(indexes[0])
        row = source_index.row()
        model = proxy_model.sourceModel()

        if isinstance(model, PandasModel):
            data = model.get_row_dict(row)
            if mode == 1:
                pipe_num = data.get("Номер трубы")
                if pipe_num and pipe_num != "Нет данных":
                    pipe_data = self.engine.get_pipe_details(str(pipe_num))
                    if pipe_data:
                        self.detail_card.set_data(pipe_data)
                        return
            self.detail_card.set_data(data)

    # Создает новую вкладку с отфильтрованными данными
    def create_filtered_tab(self, tab_name: str, filtered_df, engine: AnalyticsEngine):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tab_name:
                self.tabs.setCurrentIndex(i)
                return

        if filtered_df.empty:
            return

        temp_engine = AnalyticsEngine(filtered_df)
        display = temp_engine.get_table_data(mode=0)

        if display.empty:
            return

        tab_widget, table = self._create_table_widget()
        source_model = PandasModel(display)
        proxy_model = QSortFilterProxyModel(self.tabs)
        proxy_model.setSourceModel(source_model)
        proxy_model.setSortRole(Qt.ItemDataRole.UserRole)

        table.setModel(proxy_model)

        for i in range(len(display.columns)):
            table.setColumnHidden(i, i >= 6)

        table.resizeColumnsToContents()
        header = table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(header.ResizeMode.Stretch)

        table.selectionModel().selectionChanged.connect(
            lambda sel, des, p=proxy_model: self._on_custom_row_selected(sel, p)
        )

        if proxy_model.rowCount() > 0:
            table.selectRow(0)

        self.custom_tables.append({
            'table': table,
            'proxy': proxy_model,
            'source': source_model
        })

        self.tabs.addTab(tab_widget, tab_name)

        new_index = self.tabs.count() - 1
        close_btn = TabCloseButton()
        close_btn.clicked.connect(lambda: self.close_tab(new_index))

        self.tabs.tabBar().setTabButton(
            new_index, QTabBar.ButtonPosition.RightSide, close_btn
        )

        self.tabs.setCurrentIndex(new_index)


    # Обработчик выбора строки в кастомной таблице
    def _on_custom_row_selected(self, selected, proxy_model):
        indexes = selected.indexes()
        if not indexes:
            self.detail_card.clear()
            return

        source_index = proxy_model.mapToSource(indexes[0])
        row = source_index.row()
        model = proxy_model.sourceModel()

        if isinstance(model, PandasModel):
            self.detail_card.set_data(model.get_row_dict(row))

    # Закрывает вкладку и удаляет её из списка
    def close_tab(self, index: int):
        if index <= 1:
            return

        self.tabs.removeTab(index)
        custom_index = index - 2
        if 0 <= custom_index < len(self.custom_tables):
            self.custom_tables.pop(custom_index)

    # Сбрасывает сортировку для активной вкладки
    def reset_sorting(self, current_index: int):
        if current_index == 0:
            table, proxy = self.table_all, self.proxy_all
        elif current_index == 1:
            table, proxy = self.table_summary, self.proxy_summary
        else:
            custom_idx = current_index - 2
            if custom_idx < len(self.custom_tables):
                tab_data = self.custom_tables[custom_idx]
                table, proxy = tab_data['table'], tab_data['proxy']
            else:
                return

        if proxy is not None:
            proxy.sort(-1)
            if proxy.rowCount() > 0:
                table.selectRow(0)
