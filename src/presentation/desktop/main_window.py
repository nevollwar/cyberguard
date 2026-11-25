from pathlib import Path
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.business.managers.model_manager import (
    get_available_models,
    get_current_active_model_id,
    set_current_active_model_id,
)
from src.business.services.history_service import fetch_history, wipe_history
from src.core.config import load_config
from src.core.structures import BatchClassificationResult
from src.data.repositories.dataset_repository import save_classification_results
from src.presentation.desktop.styles import APP_STYLESHEET
from src.presentation.desktop.worker import ClassificationWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.setWindowTitle(f'{self.config.app_name} — Системный анализатор трафика (NSL-KDD)')
        self.resize(1150, 720)
        self.setStyleSheet(APP_STYLESHEET)

        self.last_result = None
        self.worker = None

        self._init_ui()
        self._load_dashboard_data()

    def _init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Левая навигационная панель
        nav_panel = QWidget()
        nav_panel.setObjectName('NavPanel')
        nav_panel.setFixedWidth(220)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        title_lbl = QLabel('🛡️ CyberGuard')
        title_lbl.setObjectName('NavTitle')
        nav_layout.addWidget(title_lbl)

        self.nav_buttons = []
        nav_items = [
            ('Главная', 0),
            ('Модели ML', 1),
            ('Классификация датасетов', 2),
            ('История запусков', 3),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName('NavButton')
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_tab(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_layout.addStretch()
        main_layout.addWidget(nav_panel)

        # 2. Правая часть со вкладками
        self.stack = QStackedWidget()
        self.stack.setObjectName('ContentArea')

        self.stack.addWidget(self._create_dashboard_tab())
        self.stack.addWidget(self._create_models_tab())
        self.stack.addWidget(self._create_classification_tab())
        self.stack.addWidget(self._create_history_tab())

        main_layout.addWidget(self.stack)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _switch_tab(self, index):
        for idx, btn in enumerate(self.nav_buttons):
            btn.setChecked(idx == index)
        self.stack.setCurrentIndex(index)
        if index == 0:
            self._load_dashboard_data()
        elif index == 3:
            self._load_history_data()

    # Вкладка 0: Dashboard
    def _create_dashboard_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header = QLabel('Панель управления системой')
        header.setObjectName('HeaderTitle')
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName('Card')
        card_layout = QVBoxLayout(card)

        self.dash_info_lbl = QLabel('Загрузка данных системы...')
        self.dash_info_lbl.setWordWrap(True)
        card_layout.addWidget(self.dash_info_lbl)
        layout.addWidget(card)

        layout.addStretch()
        return page

    def _load_dashboard_data(self):
        try:
            models = get_available_models()
            active_id = get_current_active_model_id()
            active_name = models[active_id].display_name if active_id in models else active_id
            history = fetch_history(limit=5)

            text = (
                f'<b>Статус системы:</b> Активна<br>'
                f'<b>Активная модель ML:</b> {active_name} (ID: {active_id})<br>'
                f'<b>Доступно моделей в системе:</b> {len(models)}<br>'
                f'<b>Всего запусков в истории:</b> {len(history)}<br><br>'
                f'<i>Система работает со встроенными датасетами NSL-KDD (kdd_train.csv и kdd_test.csv). '
                f'Перейдите во вкладку «Классификация датасетов» для запуска анализа.</i>'
            )
            self.dash_info_lbl.setText(text)
        except Exception as exc:
            self.dash_info_lbl.setText(f'Ошибка загрузки данных: {exc}')

    # Вкладка 1: Модели
    def _create_models_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        header = QLabel('Управление моделями машинного обучения')
        header.setObjectName('HeaderTitle')
        layout.addWidget(header)

        self.models_list = QListWidget()
        self.models_list.itemSelectionChanged.connect(self._on_model_selection_changed)
        layout.addWidget(self.models_list)

        card = QFrame()
        card.setObjectName('Card')
        card_layout = QVBoxLayout(card)

        self.model_details_lbl = QLabel('Выберите модель из списка выше.')
        self.model_details_lbl.setWordWrap(True)
        card_layout.addWidget(self.model_details_lbl)

        self.set_active_btn = QPushButton('Сделать активной моделью')
        self.set_active_btn.setObjectName('PrimaryButton')
        self.set_active_btn.clicked.connect(self._set_active_model)
        card_layout.addWidget(self.set_active_btn)

        layout.addWidget(card)
        self._load_models_list()
        return page

    def _load_models_list(self):
        self.models_list.clear()
        try:
            models = get_available_models()
            active_id = get_current_active_model_id()

            for model_id, info in models.items():
                marker = ' [АКТИВНАЯ]' if model_id == active_id else ''
                item_text = f'{info.display_name} ({model_id}){marker}'
                self.models_list.addItem(item_text)
                if model_id == active_id:
                    self.models_list.setCurrentRow(self.models_list.count() - 1)
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить список моделей: {exc}')

    def _on_model_selection_changed(self):
        items = self.models_list.selectedItems()
        if not items:
            return
        text = items[0].text()
        # Безопасно извлекаем ID из скобок (например, из "Multilayer Perceptron (MLP)" получаем "mlp")
        model_id = text.rsplit('(', 1)[1].split(')')[0]

        try:
            models = get_available_models()
            info = models.get(model_id)
            if info:
                metrics = info.metrics_test
                details = (
                    f'<b>Название:</b> {info.display_name}<br>'
                    f'<b>Описание:</b> {info.description}<br>'
                    f'<b>Размер файла модели:</b> {info.file_size_mb} МБ<br>'
                    f'<b>Метрики на тесте:</b><br>'
                    f'• Accuracy: {metrics.get("accuracy", "N/A")}<br>'
                    f'• Precision (Attack): {metrics.get("precision_attack", "N/A")}<br>'
                    f'• Recall (Attack): {metrics.get("recall_attack", "N/A")}<br>'
                    f'• F1-score (Attack): {metrics.get("f1_attack", "N/A")}'
                )
                self.model_details_lbl.setText(details)
        except Exception as exc:
            self.model_details_lbl.setText(f'Ошибка: {exc}')

    def _set_active_model(self):
        items = self.models_list.selectedItems()
        if not items:
            return
        text = items[0].text()
        model_id = text.rsplit('(', 1)[1].split(')')[0]
        try:
            set_current_active_model_id(model_id)
            QMessageBox.information(self, 'Успех', f'Активная модель изменена на: {model_id}')
            self._load_models_list()
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сменить модель: {exc}')

    # Вкладка 2: Классификация (встроенные kdd_train / kdd_test)
    def _create_classification_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        header = QLabel('Классификация датасетов NSL-KDD')
        header.setObjectName('HeaderTitle')
        layout.addWidget(header)

        # Панель выбора датасета
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel('Датасет:'))
        self.dataset_combo = QComboBox()
        self.dataset_combo.addItems([
            'Обучающая выборка (kdd_train.csv)',
            'Тестовая выборка (kdd_test.csv)'
        ])
        controls_layout.addWidget(self.dataset_combo)

        controls_layout.addWidget(QLabel('Лимит строк:'))
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(['100 строк', '1000 строк', '5000 строк', 'Весь файл'])
        controls_layout.addWidget(self.limit_combo)

        controls_layout.addStretch()

        self.run_btn = QPushButton('Запустить классификацию')
        self.run_btn.setObjectName('PrimaryButton')
        self.run_btn.clicked.connect(self._run_classification)
        controls_layout.addWidget(self.run_btn)

        layout.addLayout(controls_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Таблица результатов
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        # Нижняя панель
        bottom_layout = QHBoxLayout()
        self.stats_lbl = QLabel('Результаты: нет данных')
        bottom_layout.addWidget(self.stats_lbl)

        bottom_layout.addStretch()

        self.export_btn = QPushButton('Экспорт результатов в CSV')
        self.export_btn.setObjectName('SecondaryButton')
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_results)
        bottom_layout.addWidget(self.export_btn)

        layout.addLayout(bottom_layout)
        return page

    def _run_classification(self):
        # Определяем файл
        is_train = self.dataset_combo.currentIndex() == 0
        filename = 'kdd_train.csv' if is_train else 'kdd_test.csv'
        file_path = self.config.project_root / 'data' / 'raw' / filename

        if not file_path.exists():
            QMessageBox.critical(self, 'Ошибка', f'Файл не найден: {file_path}')
            return

        # Определяем лимит строк
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
            QMessageBox.critical(self, 'Ошибка чтения', f'Не удалось прочитать датасет: {exc}')
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        active_model = get_current_active_model_id()
        self.worker = ClassificationWorker(df, model_id=active_model, source_name=filename)
        self.worker.finished.connect(self._on_classification_finished)
        self.worker.error.connect(self._on_classification_error)
        self.worker.start()

    def _on_classification_finished(self, result: BatchClassificationResult):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.last_result = result
        self.export_btn.setEnabled(True)

        preds = result.predictions
        self.result_table.setRowCount(len(preds))
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(['№', 'Модель', 'Класс', 'Вероятность Норма', 'Вероятность Атака'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, p in enumerate(preds):
            self.result_table.setItem(i, 0, QTableWidgetItem(str(p.row_index)))
            self.result_table.setItem(i, 1, QTableWidgetItem(p.model_name))

            class_item = QTableWidgetItem(p.predicted_class)
            if p.predicted_class == 'Attack':
                class_item.setForeground(Qt.red)
            else:
                class_item.setForeground(Qt.green)
            self.result_table.setItem(i, 2, class_item)

            self.result_table.setItem(i, 3,
                                      QTableWidgetItem(str(p.prob_normal if p.prob_normal is not None else 'N/A')))
            self.result_table.setItem(i, 4,
                                      QTableWidgetItem(str(p.prob_attack if p.prob_attack is not None else 'N/A')))

        self.stats_lbl.setText(
            f'<b>Всего:</b> {result.total_count} | '
            f'<b>Норма:</b> {result.normal_count} ({result.normal_percent}%) | '
            f'<b>Атаки:</b> {result.attack_count} ({result.attack_percent}%)'
        )
        QMessageBox.information(self, 'Успех',
                                f'Классификация успешно завершена! Обработано записей: {result.total_count}')

    def _on_classification_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, 'Ошибка классификации', f'Не удалось выполнить классификацию:\n{err_msg}')

    def _export_results(self):
        if not self.last_result:
            return
        rows = []
        for p in self.last_result.predictions:
            rows.append({
                'row_index': p.row_index,
                'predicted_label': p.predicted_label,
                'predicted_class': p.predicted_class,
                'prob_normal': p.prob_normal,
                'prob_attack': p.prob_attack,
                'model_name': p.model_name
            })
        df_out = pd.DataFrame(rows)
        try:
            saved_path = save_classification_results(df_out)
            QMessageBox.information(self, 'Экспорт', f'Результаты успешно сохранены в файл:\n{saved_path}')
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить файл: {exc}')

    # Вкладка 3: История
    def _create_history_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        header = QLabel('История выполненных запусков')
        header.setObjectName('HeaderTitle')
        layout.addWidget(header)

        self.history_table = QTableWidget()
        layout.addWidget(self.history_table)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton('Обновить историю')
        refresh_btn.setObjectName('SecondaryButton')
        refresh_btn.clicked.connect(self._load_history_data)
        btn_layout.addWidget(refresh_btn)

        clear_btn = QPushButton('Очистить историю')
        clear_btn.setObjectName('SecondaryButton')
        clear_btn.clicked.connect(self._clear_history_data)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        return page

    def _load_history_data(self):
        try:
            records = fetch_history(limit=100)
            self.history_table.setRowCount(len(records))
            self.history_table.setColumnCount(7)
            self.history_table.setHorizontalHeaderLabels([
                'ID', 'Дата / Время', 'Источник', 'Модель', 'Всего', 'Норма', 'Атаки (%)'
            ])
            self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            for i, r in enumerate(records):
                self.history_table.setItem(i, 0, QTableWidgetItem(str(r.get('id'))))
                self.history_table.setItem(i, 1, QTableWidgetItem(str(r.get('created_at'))))
                self.history_table.setItem(i, 2, QTableWidgetItem(str(r.get('source_name'))))
                self.history_table.setItem(i, 3, QTableWidgetItem(str(r.get('model_name'))))
                self.history_table.setItem(i, 4, QTableWidgetItem(str(r.get('total_count'))))
                self.history_table.setItem(i, 5, QTableWidgetItem(str(r.get('normal_count'))))
                self.history_table.setItem(i, 6,
                                           QTableWidgetItem(f"{r.get('attack_count')} ({r.get('attack_percent')}%)"))
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить историю: {exc}')

    def _clear_history_data(self):
        reply = QMessageBox.question(
            self, 'Подтверждение', 'Вы уверены, что хотите полностью очистить историю запусков?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                wipe_history()
                self._load_history_data()
                QMessageBox.information(self, 'Успех', 'История успешно очищена.')
            except Exception as exc:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось очистить историю: {exc}')