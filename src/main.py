import sys
from pathlib import Path

import matplotlib

matplotlib.use("QtAgg")

from PyQt6.QtWidgets import QApplication, QMessageBox

from dashboard import DashboardWindow
from data import DataLoader


def main() -> int:
    # Создание приложения
    app = QApplication(sys.argv)
    # csv_path = Path(__file__).parent.parent / "data" / "ВсеДанныеАномалий.csv"
    csv_path = Path(__file__).parent.parent / "data" / "НаборАномалий.csv"

    # Загрузка данных
    try:
        full_data = DataLoader().load_and_clean(str(csv_path))
    except Exception as e: # noqa: BLE001
        QMessageBox.critical(None, "Ошибка загрузки данных", str(e))
        return 1

    window = DashboardWindow(full_data)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
