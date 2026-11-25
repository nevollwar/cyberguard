from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from src.core.config import load_config
from src.presentation.desktop.icons import get_icon
from src.presentation.desktop.pages.analytics_page import AnalyticsPage
from src.presentation.desktop.pages.classification_page import ClassificationPage
from src.presentation.desktop.pages.dashboard_page import DashboardPage
from src.presentation.desktop.pages.data_page import DataPage
from src.presentation.desktop.pages.history_page import HistoryPage
from src.presentation.desktop.pages.models_page import ModelsPage
from src.presentation.desktop.pages.settings_page import SettingsPage
from src.presentation.desktop.styles import APP_STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.setStyleSheet(APP_STYLESHEET)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self._init_ui()
        self.showMaximized()

    def _init_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. Верхняя панель (Title Bar)
        title_bar = QWidget(objectName='TitleBar')
        title_bar.setFixedHeight(42)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(24, 0, 14, 0)

        tb_layout.addWidget(QLabel('CyberGuard', objectName='TitleBarBrand'))
        tb_layout.addWidget(QLabel('•  Сетевой анализатор угроз NSL-KDD', objectName='TitleBarSubtitle'))
        tb_layout.addStretch()

        min_btn = QPushButton('—', objectName='WindowActionBtn')
        min_btn.setProperty('class', 'WindowActionBtn')
        min_btn.clicked.connect(self.showMinimized)
        tb_layout.addWidget(min_btn)

        max_btn = QPushButton('❐', objectName='WindowActionBtn')
        max_btn.setProperty('class', 'WindowActionBtn')
        max_btn.clicked.connect(self._toggle_maximize)
        tb_layout.addWidget(max_btn)

        close_btn = QPushButton('✕', objectName='WindowCloseBtn')
        close_btn.setProperty('class', 'WindowCloseBtn')
        close_btn.clicked.connect(self.close)
        tb_layout.addWidget(close_btn)

        root.addWidget(title_bar)

        # 2. Основная рабочая область
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Плавающее боковое меню
        sidebar_wrapper = QWidget(objectName='SidebarWrapper')
        sb_wrapper_layout = QVBoxLayout(sidebar_wrapper)
        sb_wrapper_layout.setContentsMargins(20, 4, 16, 20)

        sidebar = QFrame(objectName='Sidebar')
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(12, 22, 12, 20)
        s_layout.setSpacing(6)

        sb_title = QLabel('CyberGuard', objectName='SidebarTitle')
        sb_desc = QLabel('AI DEFENSE SYSTEM', objectName='SidebarDesc')
        s_layout.addWidget(sb_title)
        s_layout.addWidget(sb_desc)
        s_layout.addSpacing(18)

        self.nav_btns = []
        nav_items = [
            ('dashboard', 'Главная', 0),
            ('data', 'База данных', 1),
            ('models', 'Модели ИИ', 2),
            ('classification', 'Классификация', 3),
            ('analytics', 'Аналитика и OLAP', 4),
            ('history', 'Журнал аудита', 5),
            ('settings', 'Настройки', 6),
        ]

        for icon_key, title, idx in nav_items:
            btn = QPushButton(f'  {title}')
            btn.setProperty('class', 'NavBtn')
            btn.setCheckable(True)
            btn.setIconSize(QSize(18, 18))

            icon = get_icon(icon_key, color='#64748B', size=18)
            btn.setIcon(icon)

            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda ch, i=idx: self._switch_tab(i))
            s_layout.addWidget(btn)
            self.nav_btns.append((btn, icon_key))

        s_layout.addStretch()
        sb_wrapper_layout.addWidget(sidebar)
        body.addWidget(sidebar_wrapper)

        # Стек страниц
        self.stack = QStackedWidget(objectName='ContentArea')
        self.page_dash = DashboardPage()
        self.page_data = DataPage()
        self.page_models = ModelsPage(on_model_changed_callback=self._on_model_changed)
        self.page_class = ClassificationPage()
        self.page_anal = AnalyticsPage()
        self.page_hist = HistoryPage()
        self.page_sett = SettingsPage()

        self.stack.addWidget(self.page_dash)
        self.stack.addWidget(self.page_data)
        self.stack.addWidget(self.page_models)
        self.stack.addWidget(self.page_class)
        self.stack.addWidget(self.page_anal)
        self.stack.addWidget(self.page_hist)
        self.stack.addWidget(self.page_sett)

        body.addWidget(self.stack)
        root.addLayout(body)

        central = QWidget(objectName='CentralRoot')
        central.setLayout(root)
        self.setCentralWidget(central)

        self.page_dash.refresh()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _switch_tab(self, idx):
        for i, (b, icon_key) in enumerate(self.nav_btns):
            is_active = (i == idx)
            b.setChecked(is_active)
            color = '#FFFFFF' if is_active else '#64748B'
            b.setIcon(get_icon(icon_key, color=color, size=18))

        self.stack.setCurrentIndex(idx)

        if idx == 0:
            self.page_dash.refresh()
        elif idx == 2:
            self.page_models.refresh()
        elif idx == 4:
            self.page_anal.refresh()
        elif idx == 5:
            self.page_hist.refresh()

    def _on_model_changed(self):
        self.page_dash.refresh()
        self.page_anal.refresh()