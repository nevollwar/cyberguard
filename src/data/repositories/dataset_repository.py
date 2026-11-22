from datetime import datetime
from pathlib import Path

import pandas as pd

from src.core.config import AppConfig, load_config
from src.data.loaders.file_loader import read_csv_file, save_dataframe_to_csv


def load_input_csv(file_path: Path | str) -> pd.DataFrame:
    return read_csv_file(Path(file_path))


def save_classification_results(
    df_results: pd.DataFrame,
    filename: str | None = None,
    config: AppConfig | None = None,
) -> Path:
    cfg = config or load_config()
    cfg.data_results_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'cyberguard_results_{timestamp}.csv'
    elif not filename.lower().endswith('.csv'):
        filename = f'{filename}.csv'

    output_path = cfg.data_results_dir / filename
    return save_dataframe_to_csv(df_results, output_path)


def list_saved_result_files(config: AppConfig | None = None) -> list[Path]:
    cfg = config or load_config()
    if not cfg.data_results_dir.exists():
        return []
    files = list(cfg.data_results_dir.glob('*.csv'))
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)