from src.core.config import AppConfig, load_config
from src.core.exceptions import ModelLoadError, StorageError
from src.core.structures import ModelInfo
from src.data.loaders.file_loader import load_joblib_model, load_json


def load_models_info(config: AppConfig | None = None) -> dict[str, ModelInfo]:
    cfg = config or load_config()
    info_path = cfg.metadata_dir / 'models_info.json'

    try:
        raw_data = load_json(info_path)
    except StorageError as exc:
        raise ModelLoadError(f'Отсутствует или повреждён файл метаданных моделей: {info_path}') from exc

    models: dict[str, ModelInfo] = {}
    for model_id, item in raw_data.items():
        models[model_id] = ModelInfo(
            model_id=item.get('model_id', model_id),
            display_name=item.get('display_name', model_id),
            description=item.get('description', ''),
            is_default=bool(item.get('is_default', False)),
            supports_proba=bool(item.get('supports_proba', False)),
            model_path=item.get('model_path', ''),
            file_size_mb=float(item.get('file_size_mb', 0.0)),
            metrics_test=item.get('metrics_test', {}),
            trained_at=item.get('trained_at', ''),
        )
    return models


def load_feature_schema(config: AppConfig | None = None) -> dict:
    cfg = config or load_config()
    schema_path = cfg.metadata_dir / 'feature_schema.json'

    try:
        return load_json(schema_path)
    except StorageError as exc:
        raise ModelLoadError(f'Отсутствует или повреждён файл схемы признаков: {schema_path}') from exc


def load_trained_model(model_id: str, config: AppConfig | None = None):
    cfg = config or load_config()
    models = load_models_info(cfg)

    if model_id not in models:
        raise ModelLoadError(f'Модель "{model_id}" не найдена в списке доступных моделей.')

    model_rel_path = models[model_id].model_path
    full_model_path = cfg.models_dir / model_rel_path
    return load_joblib_model(full_model_path)


def get_default_model_id(config: AppConfig | None = None) -> str | None:
    models = load_models_info(config)
    for model_id, info in models.items():
        if info.is_default:
            return model_id
    if models:
        return next(iter(models.keys()))
    return None