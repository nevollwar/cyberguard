import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.api_routes import router
from src.core.config import load_config, ensure_runtime_dirs
from src.core.logger import get_logger

config = load_config()
ensure_runtime_dirs(config)
logger = get_logger('api')

app = FastAPI(
    title=f'{config.app_name} REST API',
    description='API для CyberGuard',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router, prefix='/api')


@app.get('/')
def root():
    return {
        'app': config.app_name,
        'status': 'running',
        'docs_url': '/docs',
    }


def main():
    logger.info('Запуск FastAPI на http://127.0.0.1:8000')
    # Передаем сам объект app напрямую, без reload и лишних процессов
    uvicorn.run(
        app,
        host='127.0.0.1',
        port=8000,
        log_level='info'
    )


if __name__ == '__main__':
    main()