from pathlib import Path
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.business.managers.model_manager import get_available_models, get_current_active_model_id
from src.core.config import load_config


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 32, 28)
        layout.setSpacing(18)

        # Заголовок
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel('Аналитика и многомерный OLAP-анализ', objectName='PageTitle')
        title_lbl.setProperty('class', 'PageTitle')
        desc_lbl = QLabel('Сравнение моделей, детали матрицы ошибок и многомерные срезы сетевого трафика', objectName='PageSubtitle')
        desc_lbl.setProperty('class', 'PageSubtitle')
        header_box.addWidget(title_lbl)
        header_box.addWidget(desc_lbl)
        layout.addLayout(header_box)

        # Верхние круглые вкладки
        self.sub_tabs = QTabWidget()
        self.sub_tabs.addTab(self._create_metrics_subtab(), 'СРАВНЕНИЕ МОДЕЛЕЙ')
        self.sub_tabs.addTab(self._create_matrix_subtab(), 'МАТРИЦА ОШИБОК')
        self.sub_tabs.addTab(self._create_olap_subtab(), 'МНОГОМЕРНЫЙ OLAP-КУБ')
        self.sub_tabs.addTab(self._create_charts_subtab(), 'ГРАФИКИ EDA')

        layout.addWidget(self.sub_tabs)

    def _create_metrics_subtab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.metrics_table = QTableWidget()
        layout.addWidget(self.metrics_table)
        return widget

    def _create_matrix_subtab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setProperty('class', 'BentoCard')
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 22, 24, 22)

        card_title = QLabel('Детализация матрицы ошибок (Confusion Matrix)', objectName='CardTitle')
        card_title.setProperty('class', 'CardTitle')
        c_layout.addWidget(card_title)

        self.cm_lbl = QLabel('Загрузка матрицы ошибок...')
        self.cm_lbl.setWordWrap(True)
        self.cm_lbl.setStyleSheet('color: #334155; font-size: 11pt; line-height: 2.0;')
        c_layout.addWidget(self.cm_lbl)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    def _create_olap_subtab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.olap_table = QTableWidget()
        layout.addWidget(self.olap_table)
        return widget

    def _create_charts_subtab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        self.chart1_lbl = QLabel('Загрузка графиков...')
        self.chart1_lbl.setAlignment(Qt.AlignCenter)
        self.chart2_lbl = QLabel('Загрузка графиков...')
        self.chart2_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.chart1_lbl)
        layout.addWidget(self.chart2_lbl)

        scroll.setWidget(content)
        return scroll

    def refresh(self):
        try:
            # 1. Таблица моделей
            models = get_available_models()
            self.metrics_table.setRowCount(len(models))
            self.metrics_table.setColumnCount(5)
            self.metrics_table.setHorizontalHeaderLabels(['Модель ML', 'Accuracy', 'Precision (Атака)', 'Recall (Атака)', 'F1-score (Атака)'])
            self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            for i, (m_id, info) in enumerate(models.items()):
                m = info.metrics_test
                self.metrics_table.setItem(i, 0, QTableWidgetItem(info.display_name))
                self.metrics_table.setItem(i, 1, QTableWidgetItem(str(m.get('accuracy', '—'))))
                self.metrics_table.setItem(i, 2, QTableWidgetItem(str(m.get('precision_attack', '—'))))
                self.metrics_table.setItem(i, 3, QTableWidgetItem(str(m.get('recall_attack', '—'))))
                self.metrics_table.setItem(i, 4, QTableWidgetItem(str(m.get('f1_attack', '—'))))

            # 2. Матрица ошибок
            active_id = get_current_active_model_id()
            info = models.get(active_id)
            if info and 'confusion_matrix' in info.metrics_test:
                cm = info.metrics_test['confusion_matrix']
                tn, fp = cm[0][0], cm[0][1]
                fn, tp = cm[1][0], cm[1][1]
                self.cm_lbl.setText(
                    f'Активная модель: <b style="color: #059669; font-size: 13pt;">{info.display_name}</b><br><br>'
                    f'🟢 <b>True Negative (TN):</b> {tn:,} — нормальный сетевой трафик подтверждён верно<br>'
                    f'🟡 <b>False Positive (FP):</b> {fp:,} — ложная тревога (обычный трафик принят за угрозу)<br>'
                    f'🔴 <b>False Negative (FN):</b> {fn:,} — пропущенные сетевые атаки (критическая ошибка ИБ)<br>'
                    f'🛡️ <b>True Positive (TP):</b> {tp:,} — сетевые атаки успешно обнаружены и изолированы'
                )

            # 3. OLAP-куб
            olap_path = self.config.project_root / 'data' / 'processed' / 'olap_proto_flag_cube.csv'
            if olap_path.exists():
                df_olap = pd.read_csv(olap_path)
                self.olap_table.setRowCount(len(df_olap))
                self.olap_table.setColumnCount(len(df_olap.columns))
                self.olap_table.setHorizontalHeaderLabels([str(c) for c in df_olap.columns])
                self.olap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

                for r, row in df_olap.iterrows():
                    for c, val in enumerate(row):
                        self.olap_table.setItem(r, c, QTableWidgetItem(str(val)))

            # 4. Отображение графиков (подгоняем под ширину окна)
            p1 = self.config.project_root / 'data' / 'processed' / 'correlation_heatmap.png'
            p2 = self.config.project_root / 'data' / 'processed' / 'olap_attacks_share.png'
            p3 = self.config.project_root / 'data' / 'processed' / 'eda_overview.png'

            target_img = p1 if p1.exists() else p3
            if target_img.exists():
                pix = QPixmap(str(target_img))
                self.chart1_lbl.setPixmap(pix.scaledToWidth(880, Qt.SmoothTransformation))

            if p2.exists():
                pix2 = QPixmap(str(p2))
                self.chart2_lbl.setPixmap(pix2.scaledToWidth(880, Qt.SmoothTransformation))

        except Exception as exc:
            print(f'Ошибка обновления аналитики: {exc}')