from src.core.config import AppConfig, load_config
from src.core.exceptions import ModelLoadError
from src.data.repositories.config_repository import get_active_model_id, set_active_model_id
from src.data.repositories.model_repository import (
    get_default_model_id,
    load_models_info,
    load_trained_model,
)

# Простой кэш в памяти, чтобы не загружать модель с диска при каждом запросе
_model_cache: dict[str, object] = {}


def get_available_models(config: AppConfig | None = None) -> dict:
    cfg = config or load_config()
    return load_models_info(cfg)


def get_current_active_model_id(config: AppConfig | None = None) -> str:
    cfg = config or load_config()
    active_id = get_active_model_id()

    models = get_available_models(cfg)
    if active_id and active_id in models:
        return active_id

    default_id = get_default_model_id(cfg)
    if default_id:
        set_active_model_id(default_id)
        return default_id

    raise ModelLoadError('В системе не найдено ни одной доступной модели.')


def set_current_active_model_id(model_id: str, config: AppConfig | None = None) -> None:
    cfg = config or load_config()
    models = get_available_models(cfg)

    if model_id not in models:
        raise ModelLoadError(f'Модель "{model_id}" не существует.')

    set_active_model_id(model_id)
    # Сбрасываем кэш, если модель была удалена или заменена
    if model_id in _model_cache:
        del _model_cache[model_id]


def get_active_model(config: AppConfig | None = None):
    cfg = config or load_config()
    active_id = get_current_active_model_id(cfg)

    if active_id in _model_cache:
        return _model_cache[active_id]

    model_pipeline = load_trained_model(active_id, cfg)
    _model_cache[active_id] = model_pipeline
    return model_pipeline