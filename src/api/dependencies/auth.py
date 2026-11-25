from fastapi import Header, HTTPException, status
from stc.core.config import load_config

config = load_config()

def verify_api_key(x_api_key: str | None = Header(default=None)):
    expected_token = config.api_access_token

    # Если в конфиге задан токен, обязательно требуем его совпадения
    if expected_token and x_api_key != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Доступ запрещён: неверный или отсутствующий заголовок X-API-Key'
        )
    return True