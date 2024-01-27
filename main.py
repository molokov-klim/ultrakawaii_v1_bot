import inspect
import os.path
from datetime import datetime

from email_validator import validate_email, EmailNotValidError

from aiogram import types

from aiogram.dispatcher import FSMContext

# from aiogram.utils import executor

from FSM import Form

from loguru import logger

from const.bot_link import BotLink
from const.bot_text import BotText
from const.bot_callback_data import BotCallBackData as callback
from database import create_pool, add_user, get_user, get_all_users

import config

from base import dp, bot, main_menu_keyboard
from base import Base
from handlers.command_handler import start, admin

base = Base()


# Обработчик ввода email
@dp.message_handler(state=Form.email, content_types=types.ContentTypes.TEXT)
async def process_email(message: types.Message, state: FSMContext):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    pool = base.pool
    email = message.text
    try:
        # Валидация email
        v = validate_email(email)
        valid_email = v.email
    except EmailNotValidError as error:
        await message.reply("Введенный email недействителен. Пожалуйста, попробуйте еще раз.")
        return
    await Form.category.set()  # переход к состоянию категории
    await state.update_data(email=valid_email)  # сохранение email
    # Получение всех данных о пользователе
    user_data = await state.get_data()
    user_id = message.from_user.id
    first_name = message.from_user.first_name  # Получение данных из сообщения
    last_name = message.from_user.last_name
    email = user_data.get("email")  # Получение email из FSM
    date = message.date
    # Добавление пользователя в базу данных
    async with pool.acquire() as conn:
        await add_user(conn, user_id=user_id,
                       first_name=first_name,
                       last_name=last_name,
                       email=email,
                       registration_date=date)
    await message.reply(f"{message.from_user.first_name}, твоя регистрация завершена успешно!",
                        reply_markup=main_menu_keyboard)
    await state.finish()  # Завершение FSM сессии


@dp.message_handler(lambda message: message.text == "Главное меню")
async def show_main_menu(message: types.Message):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    # Создание кнопок для выбора категории
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Услуги", callback_data=callback.SERVICES),
        types.InlineKeyboardButton("Консультация", callback_data=callback.CONSULTATION),
        types.InlineKeyboardButton("Лекции", callback_data=callback.LECTURES),
        types.InlineKeyboardButton("О нас", callback_data=callback.ABOUT),
    )

    # Отправка сообщения с кнопками
    await message.reply("Пожалуйста, выберите интересующий вас раздел:", reply_markup=markup)


# Обработчик выбора категории
@dp.callback_query_handler(lambda c: c.data in [
    callback.SERVICES,
    callback.CONSULTATION,
    callback.ABOUT,
    callback.LECTURES], state='*')
async def process_main_category(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("")  # подтверждение выбора
    await state.finish()  # завершение сессии бота

    # Отправка информационных сообщений в зависимости от выбранной категории
    if call.data == callback.SERVICES:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Агент", callback_data=callback.Services.AGENT),
            types.InlineKeyboardButton("Выкуп", callback_data=callback.Services.BUYING),
            types.InlineKeyboardButton("Доставка", callback_data=callback.Services.DELIVERY),
            types.InlineKeyboardButton("Бренд", callback_data=callback.Services.BRAND),
            types.InlineKeyboardButton("Фулфилмент", callback_data=callback.Services.FULFILLMENT),
        )
        await bot.send_message(call.message.chat.id, "Выберите подкатегорию:", reply_markup=markup)

    elif call.data == callback.CONSULTATION:
        await bot.send_message(chat_id=call.message.chat.id, text=BotText.CONSULTATION,
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == callback.ABOUT:
        await bot.send_message(chat_id=call.message.chat.id, text=BotText.ABOUT,
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == callback.LECTURES:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Мини-курс \"Бизнес с Китаем для новичков\"",
                                       callback_data=callback.Lectures.MINI_COURSE_BUSINESS_NOVICE),
            types.InlineKeyboardButton("Лекция \"ТОП 10 ошибок при закупке из Китая\"",
                                       callback_data=callback.Lectures.LECTURE_INTRO)
        )
        await bot.send_message(call.message.chat.id, "Выберите подкатегорию:", reply_markup=markup)


# services
@dp.callback_query_handler(
    lambda c: c.data in [callback.Services.AGENT,
                         callback.Services.BUYING,
                         callback.Services.DELIVERY,
                         callback.Services.BRAND,
                         callback.Services.FULFILLMENT])
async def process_services_sub_category(call: types.CallbackQuery):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("")  # подтверждение выбора

    if call.data == callback.Services.AGENT:
        await bot.send_message(call.message.chat.id,
                               text=BotText.AGENT)
    elif call.data == callback.Services.BUYING:
        await bot.send_message(chat_id=call.message.chat.id, text=BotText.BUYING,
                               parse_mode=types.ParseMode.MARKDOWN)
    elif call.data == callback.Services.DELIVERY:
        await bot.send_message(call.message.chat.id,
                               text=BotText.DELIVERY)
    elif call.data == callback.Services.BRAND:
        await bot.send_message(call.message.chat.id, text=BotText.BRAND)
    elif call.data == callback.Services.FULFILLMENT:
        await bot.send_message(call.message.chat.id, text=BotText.FULFILLMENT)


# lectures
@dp.callback_query_handler(
    lambda c: c.data in [callback.Lectures.MINI_COURSE_BUSINESS_NOVICE,
                         callback.Lectures.LECTURE_INTRO])
async def process_lectures_sub_category(call: types.CallbackQuery):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("")  # подтверждение выбора

    if call.data == callback.Lectures.MINI_COURSE_BUSINESS_NOVICE:
        await bot.send_message(call.message.chat.id, text=BotLink.LECTURE_MINI_COURSE)

    elif call.data == callback.Lectures.LECTURE_INTRO:
        await bot.send_message(call.message.chat.id, text=BotLink.LECTURE_INTRO)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    pool = base.pool
    file_id = message.document.file_id
    file_name = message.document.file_name

    if '.xls' not in str(file_name) and '.xlsx' not in str(file_name):
        await message.reply(
            f"Документ не принят. Пожалуйста используйте формат .xls или .xlsx")
        return
    await message.reply(
        f"Документ принят. Он будет передан нашей команде в обработку. Мы с вами свяжемся в ближайшее время")

    if config.SAVE_FILES:
        # Удостоверьтесь, что путь для сохранения файлов существует
        if not os.path.exists(config.FILEPATH_REQUEST_FORMS):
            os.makedirs(config.FILEPATH_REQUEST_FORMS)

        # Сохранение файла
        file_path = await bot.get_file(file_id=file_id)
        await bot.download_file(file_path=file_path.file_path,
                                destination=os.path.join(config.FILEPATH_REQUEST_FORMS,
                                                         f"{message.from_user.last_name}_{message.from_user.id}_{datetime.now().strftime('%d-%m-%Y %H-%M-%S')}_{file_name}"))

    username = ''
    try:
        username = message.from_user.username
    except Exception as error:
        logger.error(f"{inspect.currentframe().f_code.co_name}: {error}")
        pass

    user_mention = f"@{username}"
    user_id = message.from_user.id  # Получение user_id из сообщения

    async with pool.acquire() as conn:
        user_data = await get_user(conn, user_id)

    await bot.send_message(chat_id=config.ADMIN_ID, text=f'''
    Принят документ от {message.from_user.first_name} {message.from_user.last_name}\nusername: {user_mention}\nemail: {user_data['email']}
    ''')
    await bot.send_document(chat_id=config.ADMIN_ID, document=file_id)
    await bot.send_message(chat_id=config.ADMIN_2_ID, text=f'''
    Принят документ от {message.from_user.first_name} {message.from_user.last_name}\nusername: {user_mention}\nemail: {user_data['email']}
    ''')
    await bot.send_document(chat_id=config.ADMIN_2_ID, document=file_id)


@dp.message_handler(lambda message: message.text.startswith('/'), state="*")
async def unknown_command(message: types.Message, state: FSMContext):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await message.reply("Извини, я не понимаю эту команду. Я же просто бот. "
                        "Пожалуйста, используй одну из известных мне команд.",
                        reply_markup=main_menu_keyboard)
    await state.finish()  # Завершение FSM сессии


# Запуск бота
if __name__ == '__main__':
    base.start_polling()
