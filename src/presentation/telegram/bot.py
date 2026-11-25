from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from src.core.config import load_config
from src.presentation.telegram import api_client

config = load_config()
dp = Dispatcher()


def is_user_allowed(user_id: int) -> bool:
    # Если список пуст — доступ открыт для всех (удобно для тестов)
    if not config.telegram_allowed_user_ids:
        return True
    return user_id in config.telegram_allowed_user_ids


def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text='📊 Статус системы'), KeyboardButton(text='🤖 Список моделей')],
        [KeyboardButton(text='⚡ Классификация (kdd_test.csv)')],
        [KeyboardButton(text='📜 История')],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@dp.message(Command('start'))
async def cmd_start(message: Message):
    if not is_user_allowed(message.from_user.id):
        await message.answer(f'⛔ Доступ запрещён. Ваш Telegram ID: <code>{message.from_user.id}</code>', parse_mode='HTML')
        return

    text = (
        '🛡️ <b>Добро пожаловать в CyberGuard Bot!</b>\n\n'
        'Система защищённой классификации сетевого трафика NSL-KDD.\n'
        'Используйте меню ниже для управления моделями и запуска анализа.'
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode='HTML')


@dp.message(F.text == '📊 Статус системы')
@dp.message(Command('status'))
async def cmd_status(message: Message):
    if not is_user_allowed(message.from_user.id):
        await message.answer('⛔ Доступ запрещён.')
        return

    try:
        data = await api_client.fetch_status()
        text = (
            '📊 <b>Статус системы:</b>\n\n'
            f'• Сервер: <code>{data["status"].upper()}</code>\n'
            f'• Активная модель: <b>{data["active_model_name"]}</b>\n'
            f'• Доступно моделей: <b>{data["models_count"]}</b>'
        )
    except Exception as exc:
        text = f'❌ Ошибка подключения к API: {exc}'
    await message.answer(text, parse_mode='HTML')


@dp.message(F.text == '🤖 Список моделей')
@dp.message(Command('models'))
async def cmd_models(message: Message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        models = await api_client.fetch_models()
        status = await api_client.fetch_status()
        active_id = status['active_model_id']

        kb_buttons = []
        text = '🤖 <b>Доступные модели ML:</b>\n\n'

        for m in models:
            is_active = '✅ (АКТИВНАЯ)' if m['model_id'] == active_id else ''
            text += (
                f'• <b>{m["display_name"]}</b> {is_active}\n'
                f'  {m["description"]}\n'
                f'  Accuracy: <code>{m["metrics"].get("accuracy", "N/A")}</code> | '
                f'F1: <code>{m["metrics"].get("f1_attack", "N/A")}</code>\n\n'
            )
            btn_text = f'Выбрать {m["display_name"]}'
            kb_buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f'set_model:{m["model_id"]}')])

        inline_kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await message.answer(text, reply_markup=inline_kb, parse_mode='HTML')
    except Exception as exc:
        await message.answer(f'❌ Ошибка загрузки моделей: {exc}')


@dp.callback_query(F.data.startswith('set_model:'))
async def cb_set_model(query: CallbackQuery):
    if not is_user_allowed(query.from_user.id):
        await query.answer('⛔ Доступ запрещён.', show_alert=True)
        return

    model_id = query.data.split(':')[1]
    try:
        await api_client.set_active_model(model_id)
        await query.answer(f'Модель переключена на {model_id}!')
        await query.message.edit_text(f'✅ Активная модель успешно изменена на: <b>{model_id}</b>', parse_mode='HTML')
    except Exception as exc:
        await query.answer(f'Ошибка: {exc}', show_alert=True)


@dp.message(F.text == '⚡ Классификация (kdd_test.csv)')
@dp.message(Command('predict'))
async def cmd_predict(message: Message):
    if not is_user_allowed(message.from_user.id):
        return

    wait_msg = await message.answer('⏳ Выполняется классификация тестовой выборки (100 строк)...')
    try:
        res = await api_client.run_predict(dataset_name='kdd_test.csv', limit=100)
        text = (
            '⚡ <b>Результаты классификации NSL-KDD:</b>\n\n'
            f'• Модель: <b>{res["model_name"]}</b>\n'
            f'• Выборка: <code>{res["source_name"]}</code>\n'
            f'• Всего записей: <b>{res["total_count"]}</b>\n'
            f'• Норма: <b>{res["normal_count"]}</b> ({res["normal_percent"]}%)\n'
            f'• Атаки: <b>{res["attack_count"]}</b> ({res["attack_percent"]}%)'
        )
        await wait_msg.delete()
        await message.answer(text, parse_mode='HTML')
    except Exception as exc:
        await wait_msg.edit_text(f'❌ Ошибка при классификации: {exc}')


@dp.message(F.text == '📜 История')
@dp.message(Command('history'))
async def cmd_history(message: Message):
    if not is_user_allowed(message.from_user.id):
        return

    try:
        records = await api_client.fetch_history(limit=5)
        if not records:
            await message.answer('📜 История запусков пока пуста.')
            return

        text = '📜 <b>Последние запуски:</b>\n\n'
        for r in records:
            text += (
                f'🗓 <code>{r.get("created_at")}</code>\n'
                f'• Модель: {r.get("model_name")}\n'
                f'• Всего: {r.get("total_count")} | Атаки: <b>{r.get("attack_percent")}%</b>\n\n'
            )
        await message.answer(text, parse_mode='HTML')
    except Exception as exc:
        await message.answer(f'❌ Ошибка загрузки истории: {exc}')