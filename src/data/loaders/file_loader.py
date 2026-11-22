import json
from pathlib import Path

import joblib
import pandas as pd

from src.core.exceptions import DataValidationError, ModelLoadError, StorageError


def load_json(file_path: Path) -> dict:
    if not file_path.is_file():
        raise StorageError(f'Файл не найден: {file_path}')
    try:
        with file_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f'Не удалось прочитать JSON-файл {file_path.name}: {exc}') from exc


def load_joblib_model(model_path: Path):
    if not model_path.is_file():
        raise ModelLoadError(f'Файл модели не найден: {model_path}')
    try:
        return joblib.load(model_path)
    except Exception as exc:
        raise ModelLoadError(f'Не удалось загрузить модель из {model_path.name}: {exc}') from exc


def read_csv_file(file_path: Path) -> pd.DataFrame:
    if not file_path.is_file():
        raise DataValidationError(f'CSV-файл не найден: {file_path}')
    if file_path.suffix.lower() != '.csv':
        raise DataValidationError(f'Неверный формат файла "{file_path.name}". Ожидается файл с расширением .csv.')

    # Пробуем сначала стандартную UTF-8 (с BOM или без), а при ошибке кодировки — Windows-1251
    for encoding in ('utf-8-sig', 'cp1251'):
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if df.empty and len(df.columns) == 0:
                raise DataValidationError(f'Файл "{file_path.name}" пустой.')
            return df
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError as exc:
            raise DataValidationError(f'Файл "{file_path.name}" пустой и не содержит данных.') from exc
        except pd.errors.ParserError as exc:
            raise DataValidationError(f'Не удалось разобрать CSV "{file_path.name}": {exc}') from exc
        except OSError as exc:
            raise StorageError(f'Ошибка чтения файла "{file_path.name}": {exc}') from exc

    raise DataValidationError(f'Не удалось определить кодировку файла "{file_path.name}". Сохраните файл в UTF-8.')


def save_dataframe_to_csv(df: pd.DataFrame, output_path: Path) -> Path:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return output_path
    except OSError as exc:
        raise StorageError(f'Не удалось сохранить CSV в {output_path}: {exc}') from exc