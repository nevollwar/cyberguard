import sys
from PySide6.QtWidgets import QApplication
from src.core.config import load_config, ensure_runtime_dirs
from src.core.logger import get_logger
from src.presentation.desktop.main_window import MainWindow


def main():
    config = load_config()
    ensure_runtime_dirs(config)
    logger = get_logger('desktop')
    logger.info('Запуск Desktop-приложения CyberGuard')

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()