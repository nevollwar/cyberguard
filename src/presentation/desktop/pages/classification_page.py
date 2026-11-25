from pathlib import Path
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.business.managers.model_manager import get_current_active_model_id
from src.business.services.classification_service import classify_single_record
from src.core.config import load_config
from src.core.structures import BatchClassificationResult
from src.data.repositories.dataset_repository import save_classification_results
from src.data.repositories.model_repository import load_feature_schema
from src.presentation.desktop.worker import ClassificationWorker


class ClassificationPage(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.last_result = None
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 32, 28)
        layout.setSpacing(18)

        # Заголовок
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel('Классификация сетевого трафика', objectName='PageTitle')
        title_lbl.setProperty('class', 'PageTitle')
        desc_lbl = QLabel('Пакетная классификация наборов данных или экспресс-анализ параметров одиночного пакета', objectName='PageSubtitle')
        desc_lbl.setProperty('class', 'PageSubtitle')
        header_box.addWidget(title_lbl)
        header_box.addWidget(desc_lbl)
        layout.addLayout(header_box)

        tabs = QTabWidget()
        tabs.addTab(self._create_batch_tab(), 'ПАКЕТНЫЙ АНАЛИЗ (CSV)')
        tabs.addTab(self._create_single_tab(), 'ОДИНОЧНЫЙ ПАКЕТ')
        layout.addWidget(tabs)

    def _create_batch_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        # Верхняя панель запуска
        ctrl_card = QFrame()
        ctrl_card.setProperty('class', 'BentoCard')
        c_layout = QHBoxLayout(ctrl_card)
        c_layout.setContentsMargins(18, 14, 18, 14)

        c_layout.addWidget(QLabel('Датасет:'))
        self.dataset_combo = QComboBox()
        self.dataset_combo.addItems(['Боевой тест (kdd_test.csv)', 'Обучающий набор (kdd_train.csv)'])
        c_layout.addWidget(self.dataset_combo)

        c_layout.addSpacing(15)
        c_layout.addWidget(QLabel('Объём:'))
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(['100 строк', '1000 строк', '5000 строк', 'Весь файл целиком'])
        c_layout.addWidget(self.limit_combo)

        c_layout.addSpacing(15)
        self.run_btn = QPushButton('Запустить классификацию')
        self.run_btn.setProperty('class', 'PrimaryBtn')
        self.run_btn.clicked.connect(self._run_batch)
        c_layout.addWidget(self.run_btn)

        c_layout.addStretch()
        layout.addWidget(ctrl_card)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        # Нижняя плашка
        bottom_row = QHBoxLayout()
        self.stats_lbl = QLabel('Результаты: ожидание запуска')
        self.stats_lbl.setStyleSheet('color: #64748B; font-weight: 700; font-size: 10pt;')
        bottom_row.addWidget(self.stats_lbl)
        bottom_row.addStretch()

        self.export_btn = QPushButton('Экспорт результатов (CSV)')
        self.export_btn.setProperty('class', 'SecondaryBtn')
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_results)
        bottom_row.addWidget(self.export_btn)

        layout.addLayout(bottom_row)
        return widget

    def _run_batch(self):
        filename = 'kdd_test.csv' if self.dataset_combo.currentIndex() == 0 else 'kdd_train.csv'
        file_path = self.config.project_root / 'data' / 'raw' / filename

        limit_text = self.limit_combo.currentText()
        nrows = None
        if '100 ' in limit_text:
            nrows = 100
        elif '1000 ' in limit_text:
            nrows = 1000
        elif '5000 ' in limit_text:
            nrows = 5000

        try:
            df = pd.read_csv(file_path, nrows=nrows)
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка чтения', f'Не удалось прочитать файл: {exc}')
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        active_id = get_current_active_model_id()
        self.worker = ClassificationWorker(df, model_id=active_id, source_name=filename)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, result: BatchClassificationResult):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.last_result = result
        self.export_btn.setEnabled(True)

        preds = result.predictions
        self.result_table.setRowCount(len(preds))
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(['№', 'Модель', 'Вердикт', 'Вероятность Normal', 'Вероятность Attack'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, p in enumerate(preds):
            self.result_table.setItem(i, 0, QTableWidgetItem(str(p.row_index)))
            self.result_table.setItem(i, 1, QTableWidgetItem(p.model_name))

            item = QTableWidgetItem(p.predicted_class)
            if p.predicted_class == 'Attack':
                item.setForeground(Qt.red)
            else:
                item.setForeground(Qt.darkGreen)
            self.result_table.setItem(i, 2, item)

            self.result_table.setItem(i, 3, QTableWidgetItem(str(p.prob_normal if p.prob_normal is not None else '—')))
            self.result_table.setItem(i, 4, QTableWidgetItem(str(p.prob_attack if p.prob_attack is not None else '—')))

        self.stats_lbl.setText(
            f'Всего: {result.total_count:,}  |  '
            f'Норма: {result.normal_count:,} ({result.normal_percent}%)  |  '
            f'Атаки: {result.attack_count:,} ({result.attack_percent}%)'
        )

    def _on_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, 'Ошибка', f'Ошибка при классификации:\n{err_msg}')

    def _export_results(self):
        if not self.last_result:
            return
        rows = [
            {
                'row_index': p.row_index,
                'class': p.predicted_class,
                'prob_normal': p.prob_normal,
                'prob_attack': p.prob_attack,
                'model': p.model_name,
            }
            for p in self.last_result.predictions
        ]
        path = save_classification_results(pd.DataFrame(rows))
        QMessageBox.information(self, 'Успех', f'Результаты экспортированы в:\n{path}')

    def _create_single_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        header_lbl = QLabel('Параметры сетевого пакета', objectName='CardTitle')
        header_lbl.setProperty('class', 'CardTitle')
        layout.addWidget(header_lbl)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Протокол:'))
        self.single_proto = QComboBox()
        self.single_proto.addItems(['tcp', 'udp', 'icmp'])
        row1.addWidget(self.single_proto)

        row1.addWidget(QLabel('Сервис:'))
        self.single_srv = QLineEdit('http')
        row1.addWidget(self.single_srv)

        row1.addWidget(QLabel('Флаг:'))
        self.single_flag = QComboBox()
        self.single_flag.addItems(['SF', 'S0', 'REJ', 'RSTO', 'RSTR', 'SH', 'S1', 'S2', 'RSTOS0', 'S3', 'OTH'])
        row1.addWidget(self.single_flag)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel('src_bytes:'))
        self.single_src = QLineEdit('181')
        row2.addWidget(self.single_src)

        row2.addWidget(QLabel('dst_bytes:'))
        self.single_dst = QLineEdit('5450')
        row2.addWidget(self.single_dst)

        row2.addWidget(QLabel('count:'))
        self.single_count = QLineEdit('8')
        row2.addWidget(self.single_count)
        layout.addLayout(row2)

        check_btn = QPushButton('Проверить пакет')
        check_btn.setProperty('class', 'PrimaryBtn')
        check_btn.clicked.connect(self._check_single)
        layout.addWidget(check_btn)

        # Bento-карточка вердикта
        card = QFrame()
        card.setProperty('class', 'BentoCard')
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(20, 18, 20, 18)
        self.single_res_lbl = QLabel('Введите параметры и нажмите «Проверить пакет»')
        self.single_res_lbl.setStyleSheet('color: #059669; font-size: 11pt; font-weight: 700;')
        c_layout.addWidget(self.single_res_lbl)
        layout.addWidget(card)

        layout.addStretch()
        return widget

    def _check_single(self):
        try:
            schema = load_feature_schema()
            record = {feat: 0 for feat in schema['expected_features']}
            record['protocol_type'] = self.single_proto.currentText()
            record['service'] = self.single_srv.text().strip() or 'http'
            record['flag'] = self.single_flag.currentText()
            record['src_bytes'] = float(self.single_src.text().strip() or 0)
            record['dst_bytes'] = float(self.single_dst.text().strip() or 0)
            record['count'] = float(self.single_count.text().strip() or 1)

            res = classify_single_record(record)
            color = '#E11D48' if res.predicted_class == 'Attack' else '#059669'
            self.single_res_lbl.setText(
                f'Вердикт: <span style="color: {color};">{res.predicted_class.upper()}</span>  |  '
                f'Модель: {res.model_name}  |  '
                f'Вероятность атаки: {res.prob_attack if res.prob_attack is not None else "—"}'
            )
        except Exception as exc:
            self.single_res_lbl.setText(f'Ошибка: {exc}')