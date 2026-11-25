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
from src.presentation.telegram.middlewares.auth_middleware import AuthMiddleware

config = load_config()
dp = Dispatcher()

# Регистрируем проверку белого списка для всех входящих событий
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())


def is_user_allowed(user_id: int) -> bool:
    if not config.telegram_allowed_user_ids:
        return True
    return user_id in config.telegram_allowed_user_ids


def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text='📊 Статус системы'), KeyboardButton(text='🤖 Список моделей')],
        [KeyboardButton(text='⚡ Классификация (kdd_test.csv)')],
        [KeyboardButton(text='📜 История запусков')],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@dp.message(Command('start'))
async def cmd_start(message: Message):
    if not is_user_allowed(message.from_user.id):
        await message.answer(
            f'⛔ Доступ запрещён. Ваш Telegram ID: <code>{message.from_user.id}</code>',
            parse_mode='HTML',
        )
        return

    text = (
        '🛡️ <b>Добро пожаловать в CyberGuard Bot!</b>\n\n'
        'Система классификации сетевого трафика NSL-KDD.\n'
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
            kb_buttons.append(
                [InlineKeyboardButton(text=btn_text, callback_data=f'set_model:{m["model_id"]}')]
            )

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
        await query.message.edit_text(
            f'✅ Активная модель успешно изменена на: <b>{model_id}</b>', parse_mode='HTML'
        )
    except Exception as exc:
        await query.answer(f'Ошибка: {exc}', show_alert=True)


# --- Пошаговая классификация по кнопке и команде /predict ---


@dp.message(F.text == '⚡ Классификация (kdd_test.csv)')
@dp.message(Command('predict'))
async def cmd_predict_start(message: Message):
    if not is_user_allowed(message.from_user.id):
        return

    # Шаг 1: выбор датасета
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='kdd_test.csv (Боевой тест)', callback_data='choose_ds:kdd_test.csv'
                )
            ],
            [
                InlineKeyboardButton(
                    text='kdd_train.csv (Обучающий)', callback_data='choose_ds:kdd_train.csv'
                )
            ],
        ]
    )
    await message.answer('📁 <b>Выберите датасет для анализа:</b>', reply_markup=kb, parse_mode='HTML')


@dp.callback_query(F.data.startswith('choose_ds:'))
async def cb_choose_dataset(query: CallbackQuery):
    if not is_user_allowed(query.from_user.id):
        return

    dataset_name = query.data.split(':')[1]

    # Шаг 2: выбор объёма строк
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='⚡ 100 строк', callback_data=f'run_pred:{dataset_name}:100'
                ),
                InlineKeyboardButton(
                    text='📊 1 000 строк', callback_data=f'run_pred:{dataset_name}:1000'
                ),
            ],
            [
                InlineKeyboardButton(
                    text='📈 5 000 строк', callback_data=f'run_pred:{dataset_name}:5000'
                ),
                InlineKeyboardButton(
                    text='🔥 Весь датасет', callback_data=f'run_pred:{dataset_name}:all'
                ),
            ],
        ]
    )
    await query.message.edit_text(
        f'📁 Выбран датасет: <code>{dataset_name}</code>\n\n'
        f'🔢 <b>Выберите количество записей для классификации:</b>',
        reply_markup=kb,
        parse_mode='HTML',
    )


@dp.callback_query(F.data.startswith('run_pred:'))
async def cb_run_prediction(query: CallbackQuery):
    if not is_user_allowed(query.from_user.id):
        return

    _, dataset_name, limit_str = query.data.split(':')
    limit = None if limit_str == 'all' else int(limit_str)
    limit_display = 'весь файл целиком' if limit is None else f'{limit} записей'

    await query.message.edit_text(
        f'⏳ <b>Выполняется классификация...</b>\n'
        f'• Датасет: <code>{dataset_name}</code>\n'
        f'• Объём: <b>{limit_display}</b>\n\n'
        f'<i>Пожалуйста, подождите, идёт обработка данных моделью.</i>',
        parse_mode='HTML',
    )

    try:
        res = await api_client.run_predict(dataset_name=dataset_name, limit=limit)
        text = (
            '⚡ <b>Результаты классификации трафика:</b>\n\n'
            f'• Модель: <b>{res["model_name"]}</b>\n'
            f'• Выборка: <code>{res["source_name"]}</code>\n'
            f'• Всего обработано: <b>{res["total_count"]:,}</b>\n\n'
            f'🟢 <b>Нормальный трафик:</b> {res["normal_count"]:,} ({res["normal_percent"]}%)\n'
            f'🔴 <b>Обнаружено атак:</b> {res["attack_count"]:,} ({res["attack_percent"]}%)'
        )
        await query.message.edit_text(text, parse_mode='HTML')
    except Exception as exc:
        await query.message.edit_text(f'❌ Ошибка классификации: {exc}')


@dp.message(F.text == '📜 История запусков')
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
                f'• Источник: <code>{r.get("source_name")}</code>\n'
                f'• Модель: {r.get("model_name")}\n'
                f'• Всего: {r.get("total_count")} | Атаки: <b>{r.get("attack_percent")}%</b>\n\n'
            )
        await message.answer(text, parse_mode='HTML')
    except Exception as exc:
        await message.answer(f'❌ Ошибка загрузки истории: {exc}')