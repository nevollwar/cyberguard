import json
from pathlib import Path
import joblib
import pandas as pd

from src.core.exceptions import DataValidationError, ModelLoadError, StorageError

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 МБ
MAX_ROWS = 200_000
MAX_COLUMNS = 60


def load_json(file_path: Path) -> dict:
    if not file_path.is_file():
        raise StorageError(f'Файл не найден: {file_path}')
    try:
        with file_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f'Не удалось прочитать JSON-файл {file_path.name}: {exc}') from exc


def load_joblib_model(model_path: Path):
    """
    Загрузка модели через joblib с проверкой доверенной директории.
    Запрещает загрузку произвольных файлов с диска.
    """
    resolved_path = model_path.resolve()
    # Папка models лежит в корне проекта (на 3 уровня выше от файла loaders/ -> parent.parent.parent.parent)
    # Или через config.py, но для надежности берем от файла на 4 уровня вверх или через AppConfig
    from src.core.config import load_config
    config = load_config()
    project_models_dir = config.models_dir.resolve()

    try:
        resolved_path.relative_to(project_models_dir)
    except ValueError as exc:
        raise ModelLoadError(f'Безопасность: попытка загрузки модели вне доверенного хранилища: {model_path}') from exc

    if not resolved_path.is_file():
        raise ModelLoadError(f'Файл модели не найден: {resolved_path}')

    try:
        return joblib.load(resolved_path)
    except Exception as exc:
        raise ModelLoadError(f'Не удалось загрузить модель из {resolved_path.name}: {exc}') from exc


def read_csv_file(file_path: Path) -> pd.DataFrame:
    if not file_path.is_file():
        raise DataValidationError(f'CSV-файл не найден: {file_path}')
    if file_path.suffix.lower() != '.csv':
        raise DataValidationError(f'Неверный формат файла "{file_path.name}". Ожидается файл с расширением .csv.')

    # Проверка размера файла (защита от перегрузки памяти)
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise DataValidationError(
            f'Файл "{file_path.name}" слишком большой ({file_size / 1024 / 1024:.1f} МБ). Лимит: 50 МБ.')

    for encoding in ('utf-8-sig', 'cp1251'):
        try:
            # Читаем с ограничением строк и колонок
            df = pd.read_csv(file_path, encoding=encoding, nrows=MAX_ROWS)
            if df.empty or len(df.columns) == 0:
                raise DataValidationError(f'Файл "{file_path.name}" пустой.')

            if len(df.columns) > MAX_COLUMNS:
                raise DataValidationError(f'Превышено допустимое число столбцов ({len(df.columns)} > {MAX_COLUMNS}).')

            return df
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError as exc:
            raise DataValidationError(f'Файл "{file_path.name}" пустой.') from exc
        except pd.errors.ParserError as exc:
            raise DataValidationError(f'Ошибка структуры CSV в файле "{file_path.name}": {exc}') from exc
        except OSError as exc:
            raise StorageError(f'Ошибка чтения файла "{file_path.name}": {exc}') from exc

    raise DataValidationError(f'Не удалось определить кодировку файла "{file_path.name}".')


def save_dataframe_to_csv(df: pd.DataFrame, output_path: Path) -> Path:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return output_path
    except OSError as exc:
        raise StorageError(f'Не удалось сохранить CSV в {output_path}: {exc}') from exc