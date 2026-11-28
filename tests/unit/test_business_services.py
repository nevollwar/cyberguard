from pathlib import Path
import pandas as pd
import pytest

from src.business.managers.model_manager import get_available_models, load_trained_model
from src.business.services.analytics_service import calculate_batch_analytics
from src.business.validators.validation_service import validate_input_dataframe, validate_single_record
from src.core.config import _parse_user_ids, load_config
from src.core.exceptions import DataValidationError, ModelLoadError
from src.core.structures import BatchClassificationResult
from src.data.loaders.file_loader import load_joblib_model, read_csv_file
from src.data.repositories.model_repository import load_feature_schema

config = load_config()


def test_feature_schema_structure():
    schema = load_feature_schema()
    assert 'expected_features' in schema
    assert len(schema['expected_features']) == 41
    assert schema['target_column'] == 'labels'
    assert 'protocol_type' in schema['categorical_features']


def test_validate_empty_dataframe():
    empty_df = pd.DataFrame()
    with pytest.raises(DataValidationError, match='пуст'):
        validate_input_dataframe(empty_df)


def test_validate_missing_columns():
    bad_df = pd.DataFrame({'wrong_1': [1, 2], 'wrong_2': [3, 4]})
    with pytest.raises(DataValidationError, match='отсутствуют обязательные признаки'):
        validate_input_dataframe(bad_df)


def test_validate_single_record_valid():
    schema = load_feature_schema()
    rec = {col: 0 for col in schema['expected_features']}
    # Не должно выбрасывать исключений
    validate_single_record(rec)


def test_validate_single_record_empty():
    with pytest.raises(DataValidationError, match='пуста'):
        validate_single_record({})


def test_validate_single_record_missing_field():
    schema = load_feature_schema()
    rec = {col: 0 for col in schema['expected_features'][:5]}
    with pytest.raises(DataValidationError, match='отсутствуют обязательные поля'):
        validate_single_record(rec)


def test_analytics_service_calculation():
    dummy_result = BatchClassificationResult(
        model_id='mlp',
        model_name='Multilayer Perceptron',
        total_count=200,
        normal_count=150,
        attack_count=50,
        normal_percent=75.0,
        attack_percent=25.0,
    )
    analytics = calculate_batch_analytics(dummy_result)
    assert analytics['total'] == 200
    assert analytics['normal_percent'] == 75.0
    assert analytics['attack_percent'] == 25.0
    assert analytics['model_name'] == 'Multilayer Perceptron'


def test_parse_user_ids():
    raw_str = ' 12345, 67890, invalid_id, 999 '
    parsed = _parse_user_ids(raw_str)
    assert parsed == [12345, 67890, 999]


@pytest.mark.parametrize('model_id', ['logistic_regression', 'knn', 'mlp'])
def test_individual_models_loaded_and_predict(model_id):
    # Проверяем каждую модель отдельно
    pipe = load_trained_model(model_id, config)
    assert pipe is not None

    schema = load_feature_schema()
    sample = pd.DataFrame([{col: 0 for col in schema['expected_features']}])
    sample['protocol_type'] = 'tcp'
    sample['service'] = 'http'
    sample['flag'] = 'SF'

    pred = pipe.predict(sample)
    assert pred[0] in (0, 1)

    if hasattr(pipe, 'predict_proba'):
        proba = pipe.predict_proba(sample)
        assert len(proba[0]) == 2
        assert 0.0 <= proba[0][0] <= 1.0


def test_joblib_security_outside_path(tmp_path):
    # Попытка загрузить модель вне доверенной папки models/ должна блокироваться
    fake_model_file = tmp_path / 'malicious.joblib'
    fake_model_file.write_text('dummy')
    with pytest.raises(ModelLoadError, match='Безопасность'):
        load_joblib_model(fake_model_file)


def test_read_csv_file_invalid_extension(tmp_path):
    txt_file = tmp_path / 'traffic.txt'
    txt_file.write_text('col1,col2\n1,2')
    with pytest.raises(DataValidationError, match='Неверный формат'):
        read_csv_file(txt_file)


def test_read_csv_file_exceeds_columns(tmp_path):
    csv_file = tmp_path / 'wide.csv'
    cols = [f'col_{i}' for i in range(70)]
    row_data = {c: [1] for c in cols}
    pd.DataFrame(row_data).to_csv(csv_file, index=False)
    with pytest.raises(DataValidationError, match='Превышено допустимое число столбцов'):
        read_csv_file(csv_file)