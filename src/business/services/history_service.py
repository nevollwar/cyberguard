from src.core.structures import BatchClassificationResult
from src.data.repositories.history_repository import (
    add_history_record,
    clear_history,
    get_history_record_by_id,
    get_history_records,
)


def save_batch_result_to_history(result: BatchClassificationResult, exported_csv_path: str | None = None) -> int:
    summary = {
        'total': result.total_count,
        'normal': result.normal_count,
        'attack': result.attack_count,
    }

    return add_history_record(
        source_type='csv_file' if result.source_name != 'Одиночная запись' else 'single_record',
        source_name=result.source_name,
        model_id=result.model_id,
        model_name=result.model_name,
        total_count=result.total_count,
        normal_count=result.normal_count,
        attack_count=result.attack_count,
        normal_percent=result.normal_percent,
        attack_percent=result.attack_percent,
        result_summary=summary,
        exported_csv_path=exported_csv_path,
    )


def fetch_history(limit: int = 50) -> list[dict]:
    return get_history_records(limit=limit)


def fetch_history_details(record_id: int) -> dict | None:
    return get_history_record_by_id(record_id)


def wipe_history() -> int:
    return clear_history()