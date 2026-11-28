from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from src.core.config import load_config


class AuthMiddleware(BaseMiddleware):
    def __init__(self, config=None):
        super().__init__()
        self.config = config or load_config()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, 'from_user', None)

        if user is not None:
            allowed_ids = getattr(self.config, 'telegram_allowed_user_ids', [])
            if allowed_ids and user.id not in allowed_ids:
                # Если это callback-кнопка
                if isinstance(event, CallbackQuery):
                    await event.answer('⛔ Доступ запрещён.', show_alert=True)
                # Если у объекта есть метод answer (обычное сообщение или мок)
                elif hasattr(event, 'answer'):
                    await event.answer(f'⛔ Доступ запрещён. Ваш Telegram ID: {user.id}')
                return

        return await handler(event, data)