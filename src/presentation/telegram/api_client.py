import httpx
from src.core.config import load_config

config = load_config()
BASE_URL = f'{config.api_base_url}/api'


def get_client(timeout: float = 10.0) -> httpx.AsyncClient:
    # Передаём заголовок авторизации X-API-Key и отключаем прокси для локальных запросов (trust_env=False)
    headers = {'X-API-Key': config.api_access_token}
    return httpx.AsyncClient(headers=headers, timeout=timeout, trust_env=False)


async def fetch_status() -> dict:
    async with get_client() as client:
        res = await client.get(f'{BASE_URL}/status')
        res.raise_for_status()
        return res.json()


async def fetch_models() -> list[dict]:
    async with get_client() as client:
        res = await client.get(f'{BASE_URL}/models')
        res.raise_for_status()
        return res.json()


async def set_active_model(model_id: str) -> dict:
    async with get_client() as client:
        res = await client.post(f'{BASE_URL}/models/set-active', json={'model_id': model_id})
        res.raise_for_status()
        return res.json()


async def run_predict(dataset_name: str, limit: int = 100) -> dict:
    async with get_client(timeout=60.0) as client:
        res = await client.post(
            f'{BASE_URL}/predict/dataset',
            json={'dataset_name': dataset_name, 'limit': limit},
        )
        res.raise_for_status()
        return res.json()


async def fetch_history(limit: int = 5) -> list[dict]:
    async with get_client() as client:
        res = await client.get(f'{BASE_URL}/history?limit={limit}')
        res.raise_for_status()
        return res.json()