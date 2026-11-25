from pathlib import Path
import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.core.config import load_config


class DataPage(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 32, 28)
        layout.setSpacing(18)

        # Заголовок
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel('База данных трафика (NSL-KDD)', objectName='PageTitle')
        title_lbl.setProperty('class', 'PageTitle')
        desc_lbl = QLabel('Инспекция структуры, типов признаков и предпросмотр записей обучающей и тестовой выборок', objectName='PageSubtitle')
        desc_lbl.setProperty('class', 'PageSubtitle')
        header_box.addWidget(title_lbl)
        header_box.addWidget(desc_lbl)
        layout.addLayout(header_box)

        # Bento-панель управления выборкой
        ctrl_card = QFrame()
        ctrl_card.setProperty('class', 'BentoCard')
        c_layout = QHBoxLayout(ctrl_card)
        c_layout.setContentsMargins(20, 16, 20, 16)

        c_layout.addWidget(QLabel('Выборка:'))
        self.ds_combo = QComboBox()
        self.ds_combo.addItems(['Боевой тест (kdd_test.csv)', 'Обучающий набор (kdd_train.csv)'])
        c_layout.addWidget(self.ds_combo)

        c_layout.addSpacing(15)
        c_layout.addWidget(QLabel('Количество строк:'))
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(['100 строк', '500 строк', '1000 строк'])
        c_layout.addWidget(self.limit_combo)

        c_layout.addSpacing(15)
        load_btn = QPushButton('Загрузить данные')
        load_btn.setProperty('class', 'PrimaryBtn')
        load_btn.clicked.connect(self.load_data)
        c_layout.addWidget(load_btn)

        c_layout.addStretch()
        layout.addWidget(ctrl_card)

        # Bento-карточка статуса
        self.status_card = QFrame()
        self.status_card.setProperty('class', 'BentoCard')
        s_layout = QHBoxLayout(self.status_card)
        s_layout.setContentsMargins(20, 14, 20, 14)
        self.stats_lbl = QLabel('Выберите набор данных и нажмите «Загрузить данные»')
        self.stats_lbl.setStyleSheet('color: #059669; font-weight: 700; font-size: 10pt;')
        s_layout.addWidget(self.stats_lbl)
        layout.addWidget(self.status_card)

        # Таблица данных
        self.table = QTableWidget()
        layout.addWidget(self.table)

    def load_data(self):
        filename = 'kdd_test.csv' if self.ds_combo.currentIndex() == 0 else 'kdd_train.csv'
        path = self.config.project_root / 'data' / 'raw' / filename
        limit = int(self.limit_combo.currentText().split()[0])

        try:
            df = pd.read_csv(path, nrows=limit)
            nan_count = int(df.isnull().sum().sum())
            self.stats_lbl.setText(
                f'Файл: {filename}  |  Показано строк: {len(df):,}  |  '
                f'Столбцов: {len(df.columns)}  |  Пропусков (NaN): {nan_count}'
            )

            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            for r_idx, row in df.iterrows():
                for c_idx, val in enumerate(row):
                    self.table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))
        except Exception as exc:
            self.stats_lbl.setText(f'Ошибка чтения: {exc}')