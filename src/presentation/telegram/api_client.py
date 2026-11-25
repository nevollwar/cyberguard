import asyncio
from typing import Any
import httpx
from src.core.config import load_config
from src.core.logger import get_logger

config = load_config()
logger = get_logger('api_client')
BASE_URL = f'{config.api_base_url}/api'

_client: httpx.AsyncClient | None = None


def get_async_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        headers = {'X-API-Key': config.api_access_token}
        _client = httpx.AsyncClient(headers=headers, timeout=15.0, trust_env=False)
    return _client


async def close_async_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def _request_with_retry(
    method: str,
    endpoint: str,
    json: dict | None = None,  # <- принимаем именно как json
    max_retries: int = 3,
    idempotent: bool = False,
) -> Any:
    client = get_async_client()
    url = f'{BASE_URL}{endpoint}'
    delay = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            if method.upper() == 'GET':
                response = await client.get(url)
            elif method.upper() == 'POST':
                response = await client.post(url, json=json)  # передаем в httpx
            else:
                raise ValueError(f'Неподдерживаемый HTTP метод: {method}')

            if response.status_code in (401, 403, 404, 422):
                response.raise_for_status()

            response.raise_for_status()
            return response.json()

        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            is_safe_to_retry = (method.upper() == 'GET') or idempotent
            if attempt == max_retries or not is_safe_to_retry:
                logger.error(f'API запрос {method} {endpoint} не удался: {exc}')
                raise

            logger.warning(
                f'Сетевой сбой {method} {endpoint} (попытка {attempt}/{max_retries}), повтор через {delay}с'
            )
            await asyncio.sleep(delay)
            delay *= 2.0

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500 and (method.upper() == 'GET' or idempotent):
                if attempt == max_retries:
                    raise
                await asyncio.sleep(delay)
                delay *= 2.0
            else:
                raise


async def fetch_status() -> dict:
    return await _request_with_retry('GET', '/status', idempotent=True)


async def fetch_models() -> list[dict]:
    return await _request_with_retry('GET', '/models', idempotent=True)


async def set_active_model(model_id: str) -> dict:
    return await _request_with_retry(
        'POST', '/models/set-active', json={'model_id': model_id}, idempotent=True
    )


async def run_predict(dataset_name: str, limit: int | None = 100) -> dict:
    return await _request_with_retry(
        'POST',
        '/predict/dataset',
        json={'dataset_name': dataset_name, 'limit': limit},
        max_retries=2,
        idempotent=True,
    )


async def fetch_history(limit: int = 5) -> list[dict]:
    return await _request_with_retry('GET', f'/history?limit={limit}', idempotent=True)