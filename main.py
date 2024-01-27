import inspect
import logging
import os.path
from datetime import datetime

from email_validator import validate_email, EmailNotValidError

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram.utils import executor

from FSM import Form

from loguru import logger

from const.bot_link import BotLink
from const.bot_text import BotText
from database import create_pool, add_user, get_user, get_all_users

import config

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

pool = None
main_menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.add("Главное меню")


async def on_startup(dp):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    global pool
    pool = await create_pool()


# Обработчик команды /start
@dp.message_handler(commands='start', state='*')
async def cmd_start(message: types.Message):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    user_id = message.from_user.id  # Получение user_id из сообщения

    async with pool.acquire() as conn:
        user_data = await get_user(conn, user_id)

    if user_data:
        await message.reply(f"Здравствуй, {message.from_user.first_name}!", reply_markup=main_menu_keyboard)
    else:
        await Form.email.set()  # переход к состоянию имени
        await message.reply(
            f"Здравствуй, {message.from_user.first_name}! Напиши свой email для окончания регистрации.")  # отправка сообщения


# Обработчик ввода email
@dp.message_handler(state=Form.email, content_types=types.ContentTypes.TEXT)
async def process_email(message: types.Message, state: FSMContext):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
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
        types.InlineKeyboardButton("Услуги", callback_data='services'),
        types.InlineKeyboardButton("Консультация", callback_data='consultation'),
        types.InlineKeyboardButton("Лекции", callback_data='lectures'),
        types.InlineKeyboardButton("О нас", callback_data='about'),
    )

    # Отправка сообщения с кнопками
    await message.reply("Пожалуйста, выберите интересующий вас раздел:", reply_markup=markup)


# Обработчик выбора категории
@dp.callback_query_handler(lambda c: c.data in ['services', 'consultation', 'about', 'lectures'], state='*')
async def process_main_category(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("OK")  # подтверждение выбора
    await state.finish()  # завершение сессии бота

    # Отправка информационных сообщений в зависимости от выбранной категории
    if call.data == 'services':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Агент", callback_data='agent'),
            types.InlineKeyboardButton("Выкуп", callback_data='buying'),
            types.InlineKeyboardButton("Доставка", callback_data='delivery'),
            types.InlineKeyboardButton("Бренд", callback_data='brand'),
            types.InlineKeyboardButton("Фулфилмент", callback_data='fulfillment'),
        )
        await bot.send_message(call.message.chat.id, "Выберите подкатегорию:", reply_markup=markup)

    elif call.data == 'consultation':
        await bot.send_message(chat_id=call.message.chat.id, text=BotText.CONSULTATION,
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'about':
        await bot.send_message(chat_id=call.message.chat.id, text=BotText.ABOUT,
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'lectures':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Мини-курс \"Бизнес с Китаем для новичков\"",
                                       callback_data='mini_course_business_novice'),
            types.InlineKeyboardButton("Лекция \"Агент в Китае\"", callback_data='lecture_intro')
        )
        await bot.send_message(call.message.chat.id, "Выберите подкатегорию:", reply_markup=markup)


# services
@dp.callback_query_handler(
    lambda c: c.data in ['agent', 'buying', 'delivery', 'brand', 'fulfillment'])
async def process_services_sub_category(call: types.CallbackQuery):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("")  # подтверждение выбора

    if call.data == 'agent':
        await bot.send_message(call.message.chat.id,
                               text=BotText.AGENT)
    elif call.data == 'buying':
        await bot.send_message(chat_id=call.message.chat.id, text=BotText.BUYING,
                               parse_mode=types.ParseMode.MARKDOWN)
    elif call.data == 'delivery':
        await bot.send_message(call.message.chat.id,
                               text=BotText.DELIVERY)
    elif call.data == 'brand':
        await bot.send_message(call.message.chat.id, text=BotText.BRAND)
    elif call.data == 'fulfillment':
        await bot.send_message(call.message.chat.id, text=BotText.FULFILLMENT)


# lectures
@dp.callback_query_handler(
    lambda c: c.data in ['mini_course_business_novice', 'lecture_intro'])
async def process_lectures_sub_category(call: types.CallbackQuery):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("")  # подтверждение выбора

    if call.data == 'mini_course_business_novice':
        await bot.send_message(call.message.chat.id, text=BotLink.LECTURE_MINI_COURSE)

    elif call.data == 'lecture_intro':
        await bot.send_message(call.message.chat.id, text=BotLink.LECTURE_INTRO)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
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


@dp.message_handler(commands='admin', state="*")
async def admin(message: types.Message, state: FSMContext):
    logger.info(f"{inspect.currentframe().f_code.co_name}")

    user_id = message.from_user.id

    if user_id == config.ADMIN_ID or user_id == config.ADMIN_2_ID:

        async with pool.acquire() as conn:
            users_data = await get_all_users(conn)

        users_data_str = "\n".join(
            [
                f"Имя: {user_data['first_name']} {user_data['last_name']}\nEmail: {user_data['email']}\nID: {user_data['user_id']}\nДата регистрации: {user_data['registration_date']}\n\n"
                for user_data in users_data])

        await message.reply(f"{users_data_str}", reply_markup=main_menu_keyboard)

        await state.finish()  # Завершение FSM сессии

    else:
        await message.reply(f"Вы не администратор. Операция запрещена",
                            reply_markup=main_menu_keyboard)


@dp.message_handler(lambda message: message.text.startswith('/'), state="*")
async def unknown_command(message: types.Message, state: FSMContext):
    logger.info(f"{inspect.currentframe().f_code.co_name}")
    await message.reply("Извини, я не понимаю эту команду. Я же просто бот. "
                        "Пожалуйста, используй одну из известных мне команд.",
                        reply_markup=main_menu_keyboard)
    await state.finish()  # Завершение FSM сессии


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
