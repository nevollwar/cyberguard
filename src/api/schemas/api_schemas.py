from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    status: str
    active_model_id: str
    active_model_name: str
    models_count: int


class ModelInfoResponse(BaseModel):
    model_id: str
    display_name: str
    description: str
    is_default: bool
    supports_proba: bool
    file_size_mb: float
    metrics: dict = Field(default_factory=dict)


class SetActiveModelRequest(BaseModel):
    model_id: str


class PredictDatasetRequest(BaseModel):
    dataset_name: str = 'kdd_test.csv'  # kdd_train.csv или kdd_test.csv
    limit: int | None = 100
    model_id: str | None = None


class BatchPredictionResponse(BaseModel):
    model_id: str
    model_name: str
    source_name: str
    total_count: int
    normal_count: int
    attack_count: int
    normal_percent: float
    attack_percent: float