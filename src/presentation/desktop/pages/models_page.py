from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.business.managers.model_manager import (
    get_available_models,
    get_current_active_model_id,
    set_current_active_model_id,
)


class ModelsPage(QWidget):
    def __init__(self, on_model_changed_callback=None):
        super().__init__()
        self.on_model_changed = on_model_changed_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 32, 28)
        layout.setSpacing(18)

        # Заголовок
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel('Модели машинного обучения', objectName='PageTitle')
        title_lbl.setProperty('class', 'PageTitle')
        desc_lbl = QLabel('Выбор активного ядра классификации и аудит метрик качества моделей', objectName='PageSubtitle')
        desc_lbl.setProperty('class', 'PageSubtitle')
        header_box.addWidget(title_lbl)
        header_box.addWidget(desc_lbl)
        layout.addLayout(header_box)

        # Список моделей (в белой Bento-рамке)
        self.models_list = QListWidget()
        self.models_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.models_list)

        # Bento-карточка с деталями и кнопкой переключения
        card = QFrame()
        card.setProperty('class', 'BentoCard')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)

        card_title = QLabel('Спецификация и метрики выбранной модели', objectName='CardTitle')
        card_title.setProperty('class', 'CardTitle')
        card_layout.addWidget(card_title)

        self.details_lbl = QLabel('Выберите модель из списка выше для просмотра параметров.')
        self.details_lbl.setWordWrap(True)
        self.details_lbl.setStyleSheet('color: #475569; font-size: 10.5pt; line-height: 1.8;')
        card_layout.addWidget(self.details_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.set_active_btn = QPushButton('Сделать активной моделью')
        self.set_active_btn.setProperty('class', 'PrimaryBtn')
        self.set_active_btn.clicked.connect(self._set_active)
        btn_row.addWidget(self.set_active_btn)

        card_layout.addLayout(btn_row)
        layout.addWidget(card)

    def refresh(self):
        self.models_list.clear()
        try:
            models = get_available_models()
            active_id = get_current_active_model_id()

            for m_id, info in models.items():
                marker = '   ✓ [АКТИВНАЯ]' if m_id == active_id else ''
                item = QListWidgetItem(f'{info.display_name}{marker}')
                item.setData(Qt.UserRole, m_id)
                self.models_list.addItem(item)
                if m_id == active_id:
                    self.models_list.setCurrentItem(item)
        except Exception as exc:
            self.details_lbl.setText(f'Ошибка загрузки: {exc}')

    def _on_selection_changed(self):
        items = self.models_list.selectedItems()
        if not items:
            return
        m_id = items[0].data(Qt.UserRole)
        models = get_available_models()
        info = models.get(m_id)
        if not info:
            return

        m = info.metrics_test
        self.details_lbl.setText(
            f'• <b>Алгоритм:</b> {info.display_name} (ID: <code>{info.model_id}</code>)<br>'
            f'• <b>Описание:</b> {info.description}<br>'
            f'• <b>Размер файла весов:</b> {info.file_size_mb} МБ<br><br>'
            f'<b>Метрики детекции на независимом боевом тесте (kdd_test.csv):</b><br>'
            f'— Accuracy (Общая точность): <b style="color: #059669;">{m.get("accuracy", "—")}</b><br>'
            f'— Precision (Точность атак): <b>{m.get("precision_attack", "—")}</b><br>'
            f'— Recall (Полнота обнаружения атак): <b>{m.get("recall_attack", "—")}</b><br>'
            f'— F1-score (Гармоническое среднее): <b style="color: #059669;">{m.get("f1_attack", "—")}</b>'
        )

    def _set_active(self):
        items = self.models_list.selectedItems()
        if not items:
            return
        m_id = items[0].data(Qt.UserRole)
        try:
            set_current_active_model_id(m_id)
            QMessageBox.information(self, 'Успех', f'Активная модель успешно изменена на: {m_id}')
            self.refresh()
            if self.on_model_changed:
                self.on_model_changed()
        except Exception as exc:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сменить модель: {exc}')