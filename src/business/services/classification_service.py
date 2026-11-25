import pandas as pd
from src.business.managers.model_manager import (
    get_active_model,
    get_available_models,
    get_current_active_model_id,
)
from src.business.services.data_processing_service import prepare_data_for_prediction
from src.core.exceptions import ClassificationError
from src.core.logger import get_logger
from src.core.structures import BatchClassificationResult, RecordPrediction

logger = get_logger('classification_service')


def classify_dataframe(
    df: pd.DataFrame,
    model_id: str | None = None,
    source_name: str = 'Загруженный файл',
) -> BatchClassificationResult:
    try:
        active_id = model_id or get_current_active_model_id()
        models_info = get_available_models()
        model_name = models_info[active_id].display_name if active_id in models_info else active_id

        logger.info(
            f'Начало классификации: источник="{source_name}", '
            f'записей={len(df)}, модель="{model_name}" (id={active_id})'
        )

        pipeline = get_active_model()
        processed_df = prepare_data_for_prediction(df)

        predictions = pipeline.predict(processed_df)

        probabilities = None
        if hasattr(pipeline, 'predict_proba'):
            try:
                probabilities = pipeline.predict_proba(processed_df)
            except Exception:
                pass

        records = []
        normal_cnt = 0
        attack_cnt = 0

        for idx, pred in enumerate(predictions):
            pred_label = int(pred)
            class_name = 'Attack' if pred_label == 1 else 'Normal'

            if pred_label == 1:
                attack_cnt += 1
            else:
                normal_cnt += 1

            prob_normal = None
            prob_attack = None
            if probabilities is not None and len(probabilities) > idx:
                prob_normal = round(float(probabilities[idx][0]), 4)
                prob_attack = round(float(probabilities[idx][1]), 4)

            records.append(
                RecordPrediction(
                    row_index=idx + 1,
                    predicted_label=pred_label,
                    predicted_class=class_name,
                    prob_normal=prob_normal,
                    prob_attack=prob_attack,
                    model_name=model_name,
                )
            )

        total = len(records)
        normal_pct = round((normal_cnt / total * 100), 2) if total > 0 else 0.0
        attack_pct = round((attack_cnt / total * 100), 2) if total > 0 else 0.0

        logger.info(
            f'Классификация успешно завершена: всего={total}, '
            f'норма={normal_cnt} ({normal_pct}%), атаки={attack_cnt} ({attack_pct}%)'
        )

        return BatchClassificationResult(
            model_id=active_id,
            model_name=model_name,
            total_count=total,
            normal_count=normal_cnt,
            attack_count=attack_cnt,
            normal_percent=normal_pct,
            attack_percent=attack_pct,
            predictions=records,
            source_name=source_name,
        )

    except Exception as exc:
        logger.error(f'Ошибка во время выполнения классификации: {exc}')
        raise ClassificationError(f'Ошибка при выполнении классификации: {exc}') from exc


def classify_single_record(record_dict: dict, model_id: str | None = None) -> RecordPrediction:
    df = pd.DataFrame([record_dict])
    result = classify_dataframe(df, model_id=model_id, source_name='Одиночная запись')
    return result.predictions[0]