import pandas as pd
from src.business.validators.validation_service import validate_input_dataframe
from src.core.exceptions import DataValidationError
from src.data.repositories.model_repository import load_feature_schema


def prepare_data_for_prediction(df: pd.DataFrame) -> pd.DataFrame:
    validate_input_dataframe(df)
    schema = load_feature_schema()
    expected_features = schema['expected_features']
    target_col = schema['target_column']

    clean_df = df.copy()
    clean_df.columns = [str(c).strip() for c in clean_df.columns]

    # Если пользователь передал файл с целевым столбцом labels, удаляем его из признаков
    if target_col in clean_df.columns:
        clean_df = clean_df.drop(columns=[target_col])

    # Гарантируем строгий порядок столбцов, ожидаемый моделью
    for feat in expected_features:
        if feat not in clean_df.columns:
            clean_df[feat] = 0 # Защита от отсутствующих столбцов

    return clean_df[expected_features]