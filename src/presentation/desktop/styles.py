APP_STYLESHEET = """
/* Главное окно и все подложки — строго светло-серый фон */
QMainWindow, #CentralRoot, #ContentArea, QStackedWidget {
    background-color: #F4F6F9;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, Roboto, sans-serif;
    font-size: 10.5pt;
    color: #0F172A;
}

/* Верхняя строка окна (Title Bar) */
#TitleBar {
    background-color: #F4F6F9;
    padding-left: 24px;
    padding-right: 12px;
}

#TitleBarBrand {
    color: #0F172A;
    font-weight: 800;
    font-size: 11pt;
}

#TitleBarSubtitle {
    color: #64748B;
    font-size: 9pt;
    font-weight: 500;
}

QPushButton.WindowActionBtn {
    background-color: transparent;
    color: #64748B;
    border: none;
    font-size: 11pt;
    width: 36px;
    height: 30px;
    border-radius: 8px;
}

QPushButton.WindowActionBtn:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}

QPushButton.WindowCloseBtn {
    background-color: transparent;
    color: #64748B;
    border: none;
    font-size: 11pt;
    width: 36px;
    height: 30px;
    border-radius: 8px;
}

QPushButton.WindowCloseBtn:hover {
    background-color: #FEE2E2;
    color: #EF4444;
}

/* Левая боковая панель (Floating Sidebar Card) */
#SidebarWrapper {
    background-color: transparent;
    padding: 10px 0px 24px 24px;
}

#Sidebar {
    background-color: #FFFFFF;
    border-radius: 24px;
    border: 1px solid #E2E8F0;
}

#SidebarTitle {
    color: #0F172A;
    font-size: 15pt;
    font-weight: 800;
    letter-spacing: -0.5px;
}

#SidebarDesc {
    color: #64748B;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 2px;
}

/* Кнопки бокового меню */
QPushButton.NavBtn {
    background-color: transparent;
    color: #475569;
    text-align: left;
    padding: 12px 18px;
    border: none;
    font-size: 10pt;
    font-weight: 600;
    border-radius: 14px;
    margin: 3px 12px;
}

QPushButton.NavBtn:hover {
    background-color: #F8FAFC;
    color: #0F172A;
}

QPushButton.NavBtn:checked {
    background-color: #0F172A;
    color: #FFFFFF;
    font-weight: 700;
}

/* Карточки Bento Grid */
QFrame.BentoCard {
    background-color: #FFFFFF;
    border-radius: 20px;
    border: 1px solid #E2E8F0;
}

QFrame.BentoCardDark {
    background-color: #0F172A;
    border-radius: 20px;
    border: 1px solid #1E293B;
}

/* Заголовки */
QLabel.PageTitle {
    font-size: 18pt;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.4px;
    background-color: transparent;
}

QLabel.PageSubtitle {
    font-size: 10pt;
    color: #64748B;
    margin-top: 2px;
    background-color: transparent;
}

QLabel.CardTitle {
    font-size: 11pt;
    font-weight: 700;
    color: #0F172A;
    background-color: transparent;
}

/* Кнопки */
QPushButton.PrimaryBtn {
    background-color: #0F172A;
    color: #FFFFFF;
    border-radius: 12px;
    padding: 10px 22px;
    font-weight: 700;
    font-size: 9.5pt;
    border: none;
}

QPushButton.PrimaryBtn:hover {
    background-color: #1E293B;
}

QPushButton.SecondaryBtn {
    background-color: #FFFFFF;
    color: #0F172A;
    border-radius: 12px;
    padding: 10px 20px;
    font-weight: 600;
    border: 1px solid #E2E8F0;
    font-size: 9.5pt;
}

QPushButton.SecondaryBtn:hover {
    background-color: #F8FAFC;
    border-color: #CBD5E1;
}

QPushButton.DangerBtn {
    background-color: #FEE2E2;
    color: #DC2626;
    border: 1px solid #FECACA;
    border-radius: 12px;
    padding: 10px 20px;
    font-weight: 600;
}

QPushButton.DangerBtn:hover {
    background-color: #FCA5A5;
}

/* Таблицы */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    gridline-color: #F1F5F9;
    color: #0F172A;
    selection-background-color: #F1F5F9;
    selection-color: #0F172A;
}

QHeaderView::section {
    background-color: #F8FAFC;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    font-weight: 700;
    font-size: 8.5pt;
    color: #64748B;
    text-transform: uppercase;
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #F8FAFC;
}

/* Списки */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 8px;
    color: #0F172A;
}

QListWidget::item {
    padding: 12px 14px;
    border-radius: 12px;
    margin: 3px 0px;
    background-color: #F8FAFC;
}

QListWidget::item:hover {
    background-color: #F1F5F9;
}

QListWidget::item:selected {
    background-color: #0F172A;
    color: #FFFFFF;
}

/* Поля ввода */
QLineEdit, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 8px 12px;
    color: #0F172A;
    font-size: 9.5pt;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #0F172A;
}

QComboBox::drop-down {
    border: 0px;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    selection-background-color: #F1F5F9;
    selection-color: #0F172A;
    color: #0F172A;
    border-radius: 10px;
    padding: 4px;
}

/* Вкладки */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    background-color: #FFFFFF;
    border-radius: 0px 0px 20px 20px;
    top: -1px;
}

QTabBar::tab {
    background-color: #E2E8F0;
    color: #64748B;
    padding: 10px 22px;
    font-weight: 700;
    font-size: 9.5pt;
    border: 1px solid #CBD5E1;
    border-bottom: none;
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    margin-right: 4px;
}

QTabBar::tab:hover {
    background-color: #CBD5E1;
    color: #0F172A;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-bottom: none;
}

QProgressBar {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    text-align: center;
    background-color: #F1F5F9;
    color: #0F172A;
    font-weight: 700;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #059669;
    border-radius: 6px;
}
"""