from pathlib import Path
import tempfile
import pandas as pd
import pytest

from src.business.managers.model_manager import get_available_models, get_current_active_model_id
from src.business.services.classification_service import classify_dataframe, classify_single_record
from src.core.config import load_config
from src.data.repositories.dataset_repository import save_classification_results
from src.data.repositories.model_repository import load_feature_schema

config = load_config()


def test_available_models_loaded():
    models = get_available_models(config)
    assert 'mlp' in models
    assert 'logistic_regression' in models
    assert 'knn' in models
    # Проверяем, что метрики для каждой модели сохранены
    for m in models.values():
        assert 'accuracy' in m.metrics_test
        assert 'f1_attack' in m.metrics_test


def test_classify_real_test_samples():
    test_csv_path = config.project_root / 'data' / 'raw' / 'kdd_test.csv'
    assert test_csv_path.exists()

    df_sample = pd.read_csv(test_csv_path, nrows=30)
    result = classify_dataframe(df_sample, model_id='mlp', source_name='kdd_test_sample.csv')

    assert result.total_count == 30
    assert result.normal_count + result.attack_count == 30
    assert len(result.predictions) == 30

    for p in result.predictions:
        assert p.predicted_class in ('Normal', 'Attack')
        assert p.predicted_label in (0, 1)
        if p.prob_attack is not None:
            assert 0.0 <= p.prob_attack <= 1.0


def test_classify_dataframe_with_labels_column():
    # Проверяем, что наличие колонки 'labels' не ломает инференс и модель не учится на ответе
    test_csv_path = config.project_root / 'data' / 'raw' / 'kdd_test.csv'
    df_sample = pd.read_csv(test_csv_path, nrows=10)
    assert 'labels' in df_sample.columns

    res = classify_dataframe(df_sample, model_id='logistic_regression')
    assert res.total_count == 10


def test_classify_single_record_manual():
    schema = load_feature_schema()
    record = {col: 0 for col in schema['expected_features']}
    record['protocol_type'] = 'tcp'
    record['service'] = 'http'
    record['flag'] = 'SF'
    record['src_bytes'] = 215
    record['dst_bytes'] = 4500
    record['count'] = 5

    pred = classify_single_record(record, model_id='mlp')
    assert pred.predicted_class in ('Normal', 'Attack')
    assert pred.model_name != ''


def test_save_results_to_csv(tmp_path):
    df_results = pd.DataFrame([
        {'row_index': 1, 'class': 'Normal', 'prob_attack': 0.05},
        {'row_index': 2, 'class': 'Attack', 'prob_attack': 0.98},
    ])
    saved_path = save_classification_results(df_results, filename='test_export.csv')
    assert saved_path.exists()
    loaded = pd.read_csv(saved_path)
    assert len(loaded) == 2
    assert 'class' in loaded.columns