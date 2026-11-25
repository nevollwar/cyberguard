import hmac
from fastapi import Header, HTTPException, status
from src.core.config import load_config

config = load_config()


def verify_api_key(x_api_key: str | None = Header(default=None)):
    expected_token = config.api_access_token

    if not x_api_key or not hmac.compare_digest(x_api_key.encode('utf-8'), expected_token.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Доступ запрещён: неверный или отсутствующий заголовок X-API-Key'
        )
    return True