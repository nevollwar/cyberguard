APP_STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    color: #e2e8f0;
    background-color: #0f172a;
}

/* Левая навигационная панель */
#NavPanel {
    background-color: #1e293b;
    border-right: 1px solid #334155;
}

#NavTitle {
    color: #f8fafc;
    font-size: 14pt;
    font-weight: bold;
    padding: 15px;
}

QPushButton.NavButton {
    background-color: transparent;
    color: #94a3b8;
    text-align: left;
    padding: 12px 20px;
    border: none;
    font-size: 11pt;
    font-weight: 500;
}

QPushButton.NavButton:hover {
    background-color: #334155;
    color: #f8fafc;
}

QPushButton.NavButton:checked {
    background-color: #2563eb;
    color: #ffffff;
    border-left: 4px solid #60a5fa;
}

/* Основная рабочая область */
#ContentArea {
    background-color: #0f172a;
}

QFrame.Card {
    background-color: #1e293b;
    border-radius: 8px;
    border: 1px solid #334155;
    padding: 15px;
}

QLabel {
    color: #e2e8f0;
}

QLabel.HeaderTitle {
    font-size: 16pt;
    font-weight: bold;
    color: #f8fafc;
}

/* Кнопки */
QPushButton.PrimaryButton {
    background-color: #2563eb;
    color: white;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}

QPushButton.PrimaryButton:hover {
    background-color: #1d4ed8;
}

QPushButton.SecondaryButton {
    background-color: #334155;
    color: #f8fafc;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}

QPushButton.SecondaryButton:hover {
    background-color: #475569;
}

/* Таблицы и списки */
QTableWidget, QListWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #334155;
    color: #f8fafc;
}

QHeaderView::section {
    background-color: #0f172a;
    padding: 6px;
    border: none;
    font-weight: bold;
    color: #94a3b8;
}

/* Поля ввода и выпадающие списки */
QLineEdit, QComboBox, QTextEdit {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px;
    color: #f8fafc;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}

QComboBox::drop-down {
    border: 0px;
}

/* Прогресс-бар */
QProgressBar {
    border: 1px solid #475569;
    border-radius: 6px;
    text-align: center;
    background-color: #1e293b;
    color: #f8fafc;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 5px;
}
"""