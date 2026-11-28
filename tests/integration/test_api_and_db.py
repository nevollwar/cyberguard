from pathlib import Path
import tempfile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.api_routes import router
from src.core.config import load_config
from src.data.repositories.config_repository import get_active_model_id, set_active_model_id
from src.data.repositories.history_repository import add_history_record, clear_history, get_history_records
from src.presentation.telegram.middlewares.auth_middleware import AuthMiddleware

app = FastAPI()
app.include_router(router, prefix='/api')
client = TestClient(app)
config = load_config()
AUTH_HEADERS = {'X-API-Key': config.api_access_token}


def test_api_status_without_key_returns_401():
    response = client.get('/api/status')
    assert response.status_code == 401


def test_api_status_with_invalid_key_returns_401():
    response = client.get('/api/status', headers={'X-API-Key': 'fake-invalid-token'})
    assert response.status_code == 401


def test_api_status_with_valid_key_returns_200():
    response = client.get('/api/status', headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'online'
    assert 'active_model_id' in data
    assert data['models_count'] >= 3


def test_api_get_models_list():
    response = client.get('/api/models', headers=AUTH_HEADERS)
    assert response.status_code == 200
    models = response.json()
    assert len(models) >= 3
    model_ids = [m['model_id'] for m in models]
    assert 'mlp' in model_ids
    assert 'logistic_regression' in model_ids
    assert 'knn' in model_ids


def test_api_set_active_model_success():
    response = client.post('/api/models/set-active', headers=AUTH_HEADERS, json={'model_id': 'mlp'})
    assert response.status_code == 200
    assert response.json()['active_model_id'] == 'mlp'


def test_api_set_active_model_invalid():
    response = client.post('/api/models/set-active', headers=AUTH_HEADERS, json={'model_id': 'non_existing_model'})
    assert response.status_code == 400


def test_api_predict_dataset_success():
    payload = {'dataset_name': 'kdd_test.csv', 'limit': 20}
    response = client.post('/api/predict/dataset', headers=AUTH_HEADERS, json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res['total_count'] == 20
    assert res['normal_count'] + res['attack_count'] == 20


def test_api_predict_dataset_invalid_name():
    payload = {'dataset_name': 'dangerous_file.csv', 'limit': 10}
    response = client.post('/api/predict/dataset', headers=AUTH_HEADERS, json=payload)
    assert response.status_code == 400
    assert 'Недопустимый датасет' in response.json()['detail']


def test_api_history_endpoint():
    response = client.get('/api/history?limit=5', headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sqlite_history_lifecycle():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db_path = Path(f.name)

    try:
        rec_id = add_history_record(
            source_type='csv_file',
            source_name='test_traffic.csv',
            model_id='mlp',
            model_name='Multilayer Perceptron',
            total_count=50,
            normal_count=30,
            attack_count=20,
            normal_percent=60.0,
            attack_percent=40.0,
            db_path=test_db_path,
        )
        assert rec_id > 0

        records = get_history_records(limit=10, db_path=test_db_path)
        assert len(records) == 1
        assert records[0]['source_name'] == 'test_traffic.csv'

        deleted = clear_history(db_path=test_db_path)
        assert deleted == 1
        assert len(get_history_records(db_path=test_db_path)) == 0
    finally:
        test_db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_auth_middleware_blocks_unauthorized_user():
    class DummyUser:
        id = 999999999

    class DummyMessage:
        from_user = DummyUser()
        answered = False

        async def answer(self, text, **kwargs):
            self.answered = True

    middleware = AuthMiddleware()
    # Задаем список, в котором нашего пользователя нет
    middleware.config.telegram_allowed_user_ids = [111111111, 222222222]

    msg = DummyMessage()
    called = False

    async def dummy_handler(event, data):
        nonlocal called
        called = True

    await middleware(dummy_handler, msg, {})
    assert called is False, 'Хендлер не должен вызываться для чужого пользователя'
    assert msg.answered is True, 'Бот должен ответить сообщением о запрете доступа'