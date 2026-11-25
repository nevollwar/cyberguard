import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.business.managers.model_manager import get_available_models, get_current_active_model_id
from src.business.services.history_service import fetch_history


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        # Делаем страницу прокручиваемой, чтобы на любых экранах всё выглядело свободно
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 32, 28)
        layout.setSpacing(22)

        # 1. Заголовок страницы
        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        title_lbl = QLabel('Обзор безопасности', objectName='PageTitle')
        title_lbl.setProperty('class', 'PageTitle')
        desc_lbl = QLabel('Мониторинг сетевой активности, статус моделей машинного обучения и аудит угроз',
                          objectName='PageSubtitle')
        desc_lbl.setProperty('class', 'PageSubtitle')
        header_box.addWidget(title_lbl)
        header_box.addWidget(desc_lbl)
        layout.addLayout(header_box)

        # 2. Bento Grid показателей (KPI)
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)

        # Карточка 1: Активная модель (Акцентная темная Bento-карточка)
        self.card_model = QFrame()
        self.card_model.setProperty('class', 'BentoCardDark')
        cm_layout = QVBoxLayout(self.card_model)
        cm_layout.setContentsMargins(22, 20, 22, 20)

        cm_top = QHBoxLayout()
        t1 = QLabel('АКТИВНАЯ МОДЕЛЬ ИИ')
        t1.setStyleSheet('color: #94A3B8; font-weight: 800; font-size: 8.5pt; letter-spacing: 0.8px;')
        badge1 = QLabel('ВЫБРАНА')
        badge1.setStyleSheet(
            'background-color: #1E293B; color: #10B981; font-weight: 800; border-radius: 8px; padding: 4px 10px; font-size: 8pt;')
        cm_top.addWidget(t1)
        cm_top.addStretch()
        cm_top.addWidget(badge1)
        cm_layout.addLayout(cm_top)

        self.val_model = QLabel('—')
        self.val_model.setStyleSheet('color: #FFFFFF; font-size: 20pt; font-weight: 900; margin-top: 6px;')
        cm_layout.addWidget(self.val_model)
        kpi_grid.addWidget(self.card_model, 0, 0)

        # Карточка 2: Пакетов проверено
        self.val_total = QLabel('0')
        self.val_total.setStyleSheet('color: #0F172A; font-size: 22pt; font-weight: 900; margin-top: 6px;')
        kpi_grid.addWidget(
            self._make_kpi_card('ПРОВЕРЕНО ПАКЕТОВ', self.val_total, 'СКАНИРОВАНИЕ', '#F1F5F9', '#475569'), 0, 1)

        # Карточка 3: Обнаружено атак
        self.val_attacks = QLabel('0 (0%)')
        self.val_attacks.setStyleSheet('color: #E11D48; font-size: 22pt; font-weight: 900; margin-top: 6px;')
        kpi_grid.addWidget(self._make_kpi_card('ОБНАРУЖЕНО АТАК', self.val_attacks, 'УГРОЗЫ ИБ', '#FEE2E2', '#DC2626'),
                           0, 2)

        # Карточка 4: Статус защиты
        self.val_status = QLabel('ONLINE')
        self.val_status.setStyleSheet('color: #059669; font-size: 22pt; font-weight: 900; margin-top: 6px;')
        kpi_grid.addWidget(self._make_kpi_card('СТАТУС ЗАЩИТЫ', self.val_status, '3 МОДЕЛИ', '#D1FAE5', '#047857'), 0,
                           3)

        layout.addLayout(kpi_grid)

        # 3. Средний ряд: Графики аналитики
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Левая карточка (60%): Столбчатый график трафика
        chart1_card = QFrame()
        chart1_card.setProperty('class', 'BentoCard')
        c1_layout = QVBoxLayout(chart1_card)
        c1_layout.setContentsMargins(22, 20, 22, 20)

        c1_title = QLabel('Распределение трафика последней проверки', objectName='CardTitle')
        c1_title.setProperty('class', 'CardTitle')
        c1_layout.addWidget(c1_title)

        self.fig_bar = Figure(figsize=(5, 3), dpi=100)
        self.fig_bar.patch.set_facecolor('#FFFFFF')
        self.canvas_bar = FigureCanvas(self.fig_bar)
        self.ax_bar = self.fig_bar.add_subplot(111)
        c1_layout.addWidget(self.canvas_bar)

        charts_row.addWidget(chart1_card, stretch=6)

        # Правая карточка (40%): Круговая диаграмма соотношения угроз
        chart2_card = QFrame()
        chart2_card.setProperty('class', 'BentoCard')
        c2_layout = QVBoxLayout(chart2_card)
        c2_layout.setContentsMargins(22, 20, 22, 20)

        c2_title = QLabel('Соотношение угроз и нормы', objectName='CardTitle')
        c2_title.setProperty('class', 'CardTitle')
        c2_layout.addWidget(c2_title)

        self.fig_pie = Figure(figsize=(4, 3), dpi=100)
        self.fig_pie.patch.set_facecolor('#FFFFFF')
        self.canvas_pie = FigureCanvas(self.fig_pie)
        self.ax_pie = self.fig_pie.add_subplot(111)
        c2_layout.addWidget(self.canvas_pie)

        charts_row.addWidget(chart2_card, stretch=4)
        layout.addLayout(charts_row)

        # 4. Нижняя Bento-карточка: Сводка архитектуры
        bottom_card = QFrame()
        bottom_card.setProperty('class', 'BentoCard')
        b_layout = QVBoxLayout(bottom_card)
        b_layout.setContentsMargins(24, 22, 24, 22)
        b_layout.setSpacing(10)

        b_title = QLabel('Архитектурный статус платформы CyberGuard', objectName='CardTitle')
        b_title.setProperty('class', 'CardTitle')
        b_layout.addWidget(b_title)

        self.sys_desc_lbl = QLabel('Загрузка сведений о системе...')
        self.sys_desc_lbl.setWordWrap(True)
        self.sys_desc_lbl.setStyleSheet('color: #475569; font-size: 10pt; line-height: 1.7;')
        b_layout.addWidget(self.sys_desc_lbl)

        layout.addWidget(bottom_card)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _make_kpi_card(self, title_text: str, val_lbl: QLabel, badge_text: str, badge_bg: str,
                       badge_color: str) -> QFrame:
        card = QFrame()
        card.setProperty('class', 'BentoCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)

        header_row = QHBoxLayout()
        t = QLabel(title_text)
        t.setStyleSheet('color: #64748B; font-weight: 800; font-size: 8.5pt; letter-spacing: 0.8px;')
        header_row.addWidget(t)
        header_row.addStretch()

        b = QLabel(badge_text)
        b.setStyleSheet(
            f'background-color: {badge_bg}; color: {badge_color}; font-weight: 800; border-radius: 8px; padding: 4px 10px; font-size: 8pt;')
        header_row.addWidget(b)
        layout.addLayout(header_row)

        layout.addWidget(val_lbl)
        return card

    def refresh(self):
        try:
            models = get_available_models()
            active_id = get_current_active_model_id()
            active_info = models.get(active_id)
            active_name = active_info.display_name if active_info else active_id

            self.val_model.setText(active_name.split('(')[0].strip())

            history = fetch_history(limit=1)
            normal_cnt = 0
            attack_cnt = 0

            if history:
                last = history[0]
                total = last.get('total_count', 0)
                normal_cnt = last.get('normal_count', 0)
                attack_cnt = last.get('attack_count', 0)
                att_pct = last.get('attack_percent', 0.0)

                self.val_total.setText(f"{total:,}")
                self.val_attacks.setText(f"{attack_cnt:,} ({att_pct}%)")
            else:
                self.val_total.setText('—')
                self.val_attacks.setText('0 (0%)')

            self.sys_desc_lbl.setText(
                f'• <b>Активное ядро ML:</b> {active_name} (файл весов: <code>{active_info.model_path if active_info else "-"}</code>)<br>'
                f'• <b>Базовый набор данных:</b> NSL-KDD (обучающая выборка <code>kdd_train.csv</code>: 125 973 записей, независимый боевой тест <code>kdd_test.csv</code>: 22 544 записей)<br>'
                f'• <b>Конвейер нормализации:</b> StandardScaler + OneHotEncoder(ignore) + удаление константы <code>num_outbound_cmds</code><br>'
                f'• <b>Интеграция:</b> единый слой бизнес-логики подключен к Desktop-приложению и FastAPI для Telegram-бота.'
            )

            # Перерисовываем графики на чистом белом фоне
            self._render_charts(normal_cnt, attack_cnt)

        except Exception as exc:
            self.sys_desc_lbl.setText(f'Ошибка обновления дашборда: {exc}')

    def _render_charts(self, normal_cnt: int, attack_cnt: int):
        # 1. Столбчатый график
        self.ax_bar.clear()
        self.ax_bar.set_facecolor('#FFFFFF')

        categories = ['Normal', 'Attack']
        counts = [normal_cnt if (normal_cnt + attack_cnt) > 0 else 100,
                  attack_cnt if (normal_cnt + attack_cnt) > 0 else 20]
        colors = ['#10B981', '#E11D48']

        bars = self.ax_bar.bar(categories, counts, color=colors, width=0.45, edgecolor='none')
        self.ax_bar.spines['top'].set_visible(False)
        self.ax_bar.spines['right'].set_visible(False)
        self.ax_bar.spines['left'].set_color('#E2E8F0')
        self.ax_bar.spines['bottom'].set_color('#E2E8F0')
        self.ax_bar.tick_params(colors='#64748B', labelsize=9)
        self.ax_bar.grid(axis='y', linestyle='--', alpha=0.3, color='#CBD5E1')

        # Подписи над столбцами
        for bar in bars:
            height = bar.get_height()
            self.ax_bar.annotate(f'{int(height):,}',
                                 xy=(bar.get_x() + bar.get_width() / 2, height),
                                 xytext=(0, 4), textcoords="offset points",
                                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1E293B')

        self.fig_bar.tight_layout()
        self.canvas_bar.draw()

        # 2. Круговая диаграмма (Donut Chart в стиле iDraft)
        self.ax_pie.clear()
        self.ax_pie.set_facecolor('#FFFFFF')

        total = normal_cnt + attack_cnt
        if total == 0:
            pie_vals = [80, 20]
        else:
            pie_vals = [normal_cnt, attack_cnt]

        wedges, texts = self.ax_pie.pie(
            pie_vals,
            colors=['#10B981', '#E11D48'],
            startangle=90,
            wedgeprops=dict(width=0.36, edgecolor='#FFFFFF', linewidth=3)
        )
        self.ax_pie.legend(['Норма', 'Атака'], loc='lower center', bbox_to_anchor=(0.5, -0.15),
                           ncol=2, frameon=False, fontsize=9, labelcolor='#475569')

        self.fig_pie.tight_layout()
        self.canvas_pie.draw()