import pandas as pd
from PySide6.QtCore import QThread, Signal
from src.business.services.classification_service import classify_dataframe
from src.business.services.history_service import save_batch_result_to_history
from src.core.structures import BatchClassificationResult


class ClassificationWorker(QThread):
    finished = Signal(object) # Передает BatchClassificationResult
    error = Signal(str)

    def __init__(self, df: pd.DataFrame, model_id: str | None = None, source_name: str = 'Файл'):
        super().__init__()
        self.df = df
        self.model_id = model_id
        self.source_name = source_name

    def run(self):
        try:
            result: BatchClassificationResult = classify_dataframe(
                self.df, model_id=self.model_id, source_name=self.source_name
            )
            # Автоматически сохраняем результат в историю SQLite
            save_batch_result_to_history(result)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))