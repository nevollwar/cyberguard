from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from src.core.config import load_config


class AuthMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.config = load_config()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user is not None:
            allowed_ids = self.config.telegram_allowed_user_ids
            if allowed_ids and user.id not in allowed_ids:
                if isinstance(event, Message):
                    await event.answer(f'⛔ Доступ запрещён. Ваш Telegram ID: {user.id}')
                elif isinstance(event, CallbackQuery):
                    await event.answer('⛔ Доступ запрещён.', show_alert=True)
                return

        return await handler(event, data)