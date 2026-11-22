import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


# Вычисляем корень проекта (на два уровня выше папки src/core)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class AppConfig:
    app_name: str
    app_env: str
    log_level: str
    project_root: Path
    sqlite_db_path: Path
    models_dir: Path
    metadata_dir: Path
    data_results_dir: Path
    logs_dir: Path
    api_host: str
    api_port: int
    api_access_token: str
    api_base_url: str
    telegram_bot_token: str
    telegram_allowed_user_ids: list[int]


def _resolve_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _parse_user_ids(raw_ids: str) -> list[int]:
    result = []
    for item in raw_ids.split(','):
        cleaned = item.strip()
        if cleaned.isdigit():
            result.append(int(cleaned))
    return result


def load_config() -> AppConfig:
    # Подгружаем переменные из .env в корне проекта (если файла нет, сработают значения по умолчанию)
    env_path = PROJECT_ROOT / '.env'
    load_dotenv(dotenv_path=env_path)

    models_dir = _resolve_path(os.getenv('MODELS_DIR', 'models'), PROJECT_ROOT)
    sqlite_db_path = _resolve_path(os.getenv('SQLITE_DB_PATH', 'storage/cyberguard.db'), PROJECT_ROOT)
    data_results_dir = _resolve_path(os.getenv('DATA_RESULTS_DIR', 'data/results'), PROJECT_ROOT)
    logs_dir = PROJECT_ROOT / 'storage' / 'logs'

    return AppConfig(
        app_name=os.getenv('APP_NAME', 'CyberGuard'),
        app_env=os.getenv('APP_ENV', 'development'),
        log_level=os.getenv('LOG_LEVEL', 'INFO').upper(),
        project_root=PROJECT_ROOT,
        sqlite_db_path=sqlite_db_path,
        models_dir=models_dir,
        metadata_dir=models_dir / 'metadata',
        data_results_dir=data_results_dir,
        logs_dir=logs_dir,
        api_host=os.getenv('API_HOST', '127.0.0.1'),
        api_port=int(os.getenv('API_PORT', '8000')),
        api_access_token=os.getenv('API_ACCESS_TOKEN', ''),
        api_base_url=os.getenv('API_BASE_URL', 'http://127.0.0.1:8000'),
        telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
        telegram_allowed_user_ids=_parse_user_ids(os.getenv('TELEGRAM_ALLOWED_USER_IDS', '')),
    )


def ensure_runtime_dirs(config: AppConfig) -> None:
    # Создаём рабочие папки для БД, логов и сохранённых результатов, если их ещё нет
    config.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    config.data_results_dir.mkdir(parents=True, exist_ok=True)