import asyncio
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from src.core.config import load_config
from src.core.logger import get_logger
from src.presentation.telegram.bot import dp


async def main():
    config = load_config()
    logger = get_logger('telegram_bot')

    if not config.telegram_bot_token or config.telegram_bot_token.startswith('replace-'):
        logger.error('TELEGRAM_BOT_TOKEN не задан в файле .env!')
        print('\n[ОШИБКА] В файле .env не указан TELEGRAM_BOT_TOKEN.\n')
        return

    logger.info('Запуск Telegram-бота CyberGuard...')

    session = None
    if config.telegram_proxy_url:
        logger.info(f'Использование прокси для Telegram: {config.telegram_proxy_url}')
        session = AiohttpSession(proxy=config.telegram_proxy_url)

    bot = Bot(token=config.telegram_bot_token, session=session)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('\nTelegram-бот успешно остановлен.')