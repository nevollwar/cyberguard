import pandas as pd
from src.core.exceptions import DataValidationError
from src.data.repositories.model_repository import load_feature_schema


def validate_input_dataframe(df: pd.DataFrame) -> None:
    if df.empty:
        raise DataValidationError('Загруженный датасет пуст (нет строк).')

    schema = load_feature_schema()
    expected_features = schema['expected_features']  # 41 признак
    target_col = schema['target_column']  # 'labels'

    df_columns_cleaned = [str(col).strip() for col in df.columns]

    # Если в файле присутствует целевой столбец labels, это допустимо (по ТЗ мы его просто не используем),
    # но проверим, что хотя бы основные обязательные признаки на месте.
    missing_features = [
        feat for feat in expected_features
        if feat not in df_columns_cleaned and feat != target_col
    ]

    if missing_features:
        raise DataValidationError(
            f'Во входных данных отсутствуют обязательные признаки ({len(missing_features)} шт.): '
            f'{", ".join(missing_features[:5])}{"..." if len(missing_features) > 5 else ""}'
        )


def validate_single_record(record_dict: dict) -> None:
    if not record_dict:
        raise DataValidationError('Запись для классификации пуста.')

    schema = load_feature_schema()
    expected_features = schema['expected_features']

    missing = [f for f in expected_features if f not in record_dict and f != schema['target_column']]
    if missing:
        raise DataValidationError(f'В записи отсутствуют обязательные поля: {", ".join(missing[:5])}')