from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.business.services.history_service import fetch_history, wipe_history


class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 32, 28)
        layout.setSpacing(18)

        # Заголовок
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel('Журнал аудита классификаций', objectName='PageTitle')
        title_lbl.setProperty('class', 'PageTitle')
        desc_lbl = QLabel('Хронология всех выполненных сессий сканирования и проверок сетевого трафика', objectName='PageSubtitle')
        desc_lbl.setProperty('class', 'PageSubtitle')
        header_box.addWidget(title_lbl)
        header_box.addWidget(desc_lbl)
        layout.addLayout(header_box)

        # Bento-панель поиска
        ctrl_card = QFrame()
        ctrl_card.setProperty('class', 'BentoCard')
        c_layout = QHBoxLayout(ctrl_card)
        c_layout.setContentsMargins(18, 14, 18, 14)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Поиск по названию модели или файлу источника...')
        self.search_input.textChanged.connect(self._filter)
        c_layout.addWidget(self.search_input, stretch=1)

        c_layout.addSpacing(15)
        refresh_btn = QPushButton('Обновить')
        refresh_btn.setProperty('class', 'SecondaryBtn')
        refresh_btn.clicked.connect(self.refresh)
        c_layout.addWidget(refresh_btn)

        clear_btn = QPushButton('Очистить журнал')
        clear_btn.setProperty('class', 'DangerBtn')
        clear_btn.clicked.connect(self._clear)
        c_layout.addWidget(clear_btn)

        layout.addWidget(ctrl_card)

        # Таблица истории
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.raw_records = []

    def refresh(self):
        self.raw_records = fetch_history(limit=100)
        self._populate(self.raw_records)

    def _populate(self, records):
        self.table.setRowCount(len(records))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['ID', 'Дата / Время', 'Источник', 'Модель ИИ', 'Всего', 'Норма', 'Атаки (%)'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, r in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.get('id'))))
            self.table.setItem(i, 1, QTableWidgetItem(str(r.get('created_at'))))
            self.table.setItem(i, 2, QTableWidgetItem(str(r.get('source_name'))))
            self.table.setItem(i, 3, QTableWidgetItem(str(r.get('model_name'))))
            self.table.setItem(i, 4, QTableWidgetItem(f"{r.get('total_count'):,}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{r.get('normal_count'):,}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{r.get('attack_count'):,} ({r.get('attack_percent')}%)"))

    def _filter(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate(self.raw_records)
            return
        filtered = [
            r for r in self.raw_records
            if query in str(r.get('source_name', '')).lower() or query in str(r.get('model_name', '')).lower()
        ]
        self._populate(filtered)

    def _clear(self):
        reply = QMessageBox.question(self, 'Подтверждение', 'Вы действительно хотите удалить все записи журнала аудита?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            wipe_history()
            self.refresh()