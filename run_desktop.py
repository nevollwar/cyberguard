import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from src.core.config import load_config, ensure_runtime_dirs
from src.core.logger import get_logger
from src.presentation.desktop.main_window import MainWindow


def main():
    config = load_config()
    ensure_runtime_dirs(config)
    logger = get_logger('desktop')
    logger.info('Запуск Desktop-приложения CyberGuard')

    app = QApplication(sys.argv)

    # ПРИНУДИТЕЛЬНО ВКЛЮЧАЕМ СВЕТЛУЮ ТЕМУ (игнорируем темную тему Windows)
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor('#F4F6F9'))
    palette.setColor(QPalette.WindowText, QColor('#0F172A'))
    palette.setColor(QPalette.Base, QColor('#FFFFFF'))
    palette.setColor(QPalette.AlternateBase, QColor('#F8FAFC'))
    palette.setColor(QPalette.ToolTipBase, QColor('#FFFFFF'))
    palette.setColor(QPalette.ToolTipText, QColor('#0F172A'))
    palette.setColor(QPalette.Text, QColor('#0F172A'))
    palette.setColor(QPalette.Button, QColor('#FFFFFF'))
    palette.setColor(QPalette.ButtonText, QColor('#0F172A'))
    palette.setColor(QPalette.Highlight, QColor('#0F172A'))
    palette.setColor(QPalette.HighlightedText, QColor('#FFFFFF'))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()