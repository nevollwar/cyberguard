import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies.auth import verify_api_key
from src.api.schemas.api_schemas import (
    BatchPredictionResponse,
    ModelInfoResponse,
    PredictDatasetRequest,
    SetActiveModelRequest,
    SystemStatusResponse,
)
from src.business.managers.model_manager import (
    get_available_models,
    get_current_active_model_id,
    set_current_active_model_id,
)
from src.business.services.classification_service import classify_dataframe
from src.business.services.history_service import fetch_history, save_batch_result_to_history
from src.core.config import load_config

# Все роуты автоматически защищаются заголовком X-API-Key
router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get('/status', response_model=SystemStatusResponse)
def get_status():
    models = get_available_models()
    active_id = get_current_active_model_id()
    active_name = models[active_id].display_name if active_id in models else active_id

    return SystemStatusResponse(
        status='online',
        active_model_id=active_id,
        active_model_name=active_name,
        models_count=len(models),
    )


@router.get('/models', response_model=list[ModelInfoResponse])
def list_models():
    models = get_available_models()
    result = []
    for m_id, info in models.items():
        result.append(
            ModelInfoResponse(
                model_id=m_id,
                display_name=info.display_name,
                description=info.description,
                is_default=info.is_default,
                supports_proba=info.supports_proba,
                file_size_mb=info.file_size_mb,
                metrics=info.metrics_test,
            )
        )
    return result


@router.post('/models/set-active')
def set_active_model(req: SetActiveModelRequest):
    try:
        set_current_active_model_id(req.model_id)
        return {'success': True, 'active_model_id': req.model_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post('/predict/dataset', response_model=BatchPredictionResponse)
def predict_dataset(req: PredictDatasetRequest):
    config = load_config()
    allowed_files = {'kdd_train.csv', 'kdd_test.csv'}

    if req.dataset_name not in allowed_files:
        raise HTTPException(
            status_code=400, detail=f'Недопустимый датасет. Выберите один из: {", ".join(allowed_files)}'
        )

    file_path = config.project_root / 'data' / 'raw' / req.dataset_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f'Файл {req.dataset_name} не найден на сервере.')

    try:
        # Если req.limit == None, read_csv прочитает весь файл целиком
        df = pd.read_csv(file_path, nrows=req.limit)
        result = classify_dataframe(
            df, model_id=req.model_id, source_name=f'{req.dataset_name} (API)'
        )
        save_batch_result_to_history(result)

        return BatchPredictionResponse(
            model_id=result.model_id,
            model_name=result.model_name,
            source_name=result.source_name,
            total_count=result.total_count,
            normal_count=result.normal_count,
            attack_count=result.attack_count,
            normal_percent=result.normal_percent,
            attack_percent=result.attack_percent,
        )
    except Exception as exc:
        # Выведи точный трейсбек в консоль сервера для отладки
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f'Ошибка классификации: {exc}')


@router.get('/history')
def get_history(limit: int = 10):
    return fetch_history(limit=limit)