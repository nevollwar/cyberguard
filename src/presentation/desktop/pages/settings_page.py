from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
from src.core.config import load_config


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        config = load_config()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 32, 28)
        layout.setSpacing(18)

        # Заголовок
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel('Конфигурация и среда', objectName='PageTitle')
        title_lbl.setProperty('class', 'PageTitle')
        desc_lbl = QLabel('Спецификация хранилищ данных, сетевых портов API и параметров окружения', objectName='PageSubtitle')
        desc_lbl.setProperty('class', 'PageSubtitle')
        header_box.addWidget(title_lbl)
        header_box.addWidget(desc_lbl)
        layout.addLayout(header_box)

        # Белая Bento-карточка
        card = QFrame()
        card.setProperty('class', 'BentoCard')
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(26, 24, 26, 24)
        c_layout.setSpacing(14)

        card_title = QLabel('Параметры среды выполнения платформы', objectName='CardTitle')
        card_title.setProperty('class', 'CardTitle')
        c_layout.addWidget(card_title)

        text = (
            f'• <b>Система:</b> CyberGuard (версия 1.0.0)<br>'
            f'• <b>База данных SQLite:</b> <code>{config.sqlite_db_path}</code><br>'
            f'• <b>Каталог обученных моделей:</b> <code>{config.models_dir}</code><br>'
            f'• <b>Каталог экспортированных отчётов:</b> <code>{config.data_results_dir}</code><br>'
            f'• <b>Каталог журнала аудита:</b> <code>{config.logs_dir}</code><br>'
            f'• <b>Сервер REST API:</b> <code>http://{config.api_host}:{config.api_port}</code><br>'
            f'• <b>Авторизация API:</b> Защищено секретным токеном (X-API-Key)'
        )
        lbl = QLabel(text)
        lbl.setStyleSheet('line-height: 2.1; color: #334155; font-size: 10.5pt;')
        c_layout.addWidget(lbl)

        layout.addWidget(card)
        layout.addStretch()