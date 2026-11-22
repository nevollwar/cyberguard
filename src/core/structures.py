from dataclasses import dataclass, field


# Структуры данных для обмена информацией между слоями приложения


@dataclass
class ModelInfo:
    model_id: str
    display_name: str
    description: str
    is_default: bool
    supports_proba: bool
    model_path: str
    file_size_mb: float
    metrics_test: dict = field(default_factory=dict)
    trained_at: str = ''


@dataclass
class RecordPrediction:
    row_index: int
    predicted_label: int
    predicted_class: str
    prob_normal: float | None
    prob_attack: float | None
    model_name: str


@dataclass
class BatchClassificationResult:
    model_id: str
    model_name: str
    total_count: int
    normal_count: int
    attack_count: int
    normal_percent: float
    attack_percent: float
    predictions: list[RecordPrediction] = field(default_factory=list)
    source_name: str = ''
    created_at: str = ''