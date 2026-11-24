from src.core.structures import BatchClassificationResult


def calculate_batch_analytics(result: BatchClassificationResult) -> dict:
    return {
        'total': result.total_count,
        'normal_count': result.normal_count,
        'attack_count': result.attack_count,
        'normal_percent': result.normal_percent,
        'attack_percent': result.attack_percent,
        'model_name': result.model_name
    }