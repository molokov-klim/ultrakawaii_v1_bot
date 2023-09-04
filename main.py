import logging

import asyncpg
from email_validator import validate_email, EmailNotValidError

import config
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from database import create_pool, add_user, get_user

# Настройка логгирования
logging.basicConfig(level=logging.INFO, filename='bot.log')

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

pool = None
main_menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.add("Главное меню")


async def on_startup(dp):
    global pool
    pool = await create_pool()


# Определение состояний для машины состояний
class Form(StatesGroup):
    email = State()  # состояние для email
    category = State()  # состояние для категории


# Обработчик команды /start
@dp.message_handler(commands='start', state='*')
async def cmd_start(message: types.Message):
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
    # await message.reply("Вы успешно зарегистрированы! Пожалуйста, выберите интересующий вас раздел:",
    #                     reply_markup=main_menu_keyboard)  # Используйте main_menu_keyboard здесь
    await message.reply(f"{message.from_user.first_name}, твоя регистрация завершена успешно!",
                        reply_markup=main_menu_keyboard)
    await state.finish()  # Завершение FSM сессии


# Обработчик выбора категории
@dp.callback_query_handler(lambda c: c.data in ['services', 'training', 'gifts', 'minicourse'], state='*')
async def process_main_category(call: types.CallbackQuery, state: FSMContext):
    await call.answer("Вы выбрали раздел.")  # подтверждение выбора
    await state.finish()  # завершение сессии бота

    # Отправка информационных сообщений в зависимости от выбранной категории
    if call.data == 'services':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("1 Поиск поставщиков и товаров", callback_data='find_suppliers'),
            types.InlineKeyboardButton("2 Агент по закупкам", callback_data='purchase_agent'),
            types.InlineKeyboardButton("3 Проверка фабрики", callback_data='factory_check'),
            types.InlineKeyboardButton("4 Доставка и таможенное оформление", callback_data='customs'),
            types.InlineKeyboardButton("5 Бренд под ключ", callback_data='turnkey_brand'),
        )
        await bot.send_message(call.message.chat.id, "Выберите подкатегорию:", reply_markup=markup)

    elif call.data == 'training':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("1 Экспресс консультация 8 888 руб", callback_data='express_consultation'),
            types.InlineKeyboardButton("2 Персональная сессия 16 888 руб", callback_data='personal_session'),
            types.InlineKeyboardButton("3 Большая консультация 58 888 руб", callback_data='big_consultation'),
            types.InlineKeyboardButton("4 Наставничество 208 888 руб", callback_data='mentorship')
        )
        await bot.send_message(call.message.chat.id, "Выберите вид обучения:", reply_markup=markup)
    elif call.data == 'gifts':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Рабочая тетрадь какой товар везти из Китая", callback_data='workbook'),
            types.InlineKeyboardButton("Вводная лекция", callback_data='intro_lecture')
        )
        await bot.send_message(call.message.chat.id, "Выберите подарок:", reply_markup=markup)
    elif call.data == 'minicourse':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Запись курса лекций по закупкам товаров в Китае без обратной связи 6888 руб",
                                       callback_data='minicourse_lectures')
        )
        await bot.send_message(call.message.chat.id, "Выберите мини-курс:", reply_markup=markup)


@dp.message_handler(lambda message: message.text == "Главное меню")
async def show_main_menu(message: types.Message):
    print("show_main_menu()")
    # Создание кнопок для выбора категории
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Услуги и цены", callback_data='services'),
        types.InlineKeyboardButton("Обучение", callback_data='training'),
        types.InlineKeyboardButton("Подарки", callback_data='gifts'),
        types.InlineKeyboardButton("Мини-курс", callback_data='minicourse')
    )

    # Отправка сообщения с кнопками
    await message.reply("Пожалуйста, выберите интересующий вас раздел:", reply_markup=markup)


@dp.callback_query_handler(
    lambda c: c.data in ['find_suppliers', 'purchase_agent', 'factory_check', 'customs', 'turnkey_brand'])
async def process_services_sub_category(call: types.CallbackQuery):
    await call.answer("Вы выбрали подкатегорию.")  # подтверждение выбора

    if call.data == 'find_suppliers':
        await bot.send_message(call.message.chat.id, "Форма и описание для поиска поставщиков и товаров...")
    elif call.data == 'purchase_agent':
        await bot.send_message(call.message.chat.id, "Описание услуги агента по закупкам...")
    elif call.data == 'factory_check':
        await bot.send_message(call.message.chat.id, "Описание проверки фабрики...")
    elif call.data == 'customs':
        await bot.send_message(call.message.chat.id, "Описание доставки и таможенного оформления...")
    elif call.data == 'turnkey_brand':
        await bot.send_message(call.message.chat.id, "Описание услуги 'Бренд под ключ'..,")


@dp.callback_query_handler(
    lambda c: c.data in ['express_consultation', 'personal_session', 'big_consultation', 'mentorship'])
async def process_training_sub_category(call: types.CallbackQuery):
    await call.answer("Вы выбрали вид обучения.")  # подтверждение выбора

    if call.data == 'express_consultation':
        await bot.send_message(call.message.chat.id, "Полное описание Экспресс консультации...")
    elif call.data == 'personal_session':
        await bot.send_message(call.message.chat.id, "Полное описание Персональной сессии...")
    elif call.data == 'big_consultation':
        await bot.send_message(call.message.chat.id, "Полное описание Большой консультации...")
    elif call.data == 'mentorship':
        await bot.send_message(call.message.chat.id, "Полное описание Наставничества...")


@dp.callback_query_handler(lambda c: c.data in ['workbook', 'intro_lecture'])
async def process_gifts_sub_category(call: types.CallbackQuery):
    await call.answer("Вы выбрали подарок.")  # подтверждение выбора

    if call.data == 'workbook':
        await bot.send_message(call.message.chat.id, "Полное описание рабочей тетради 'Какой товар везти из Китая'...")
    elif call.data == 'intro_lecture':
        await bot.send_message(call.message.chat.id, "Полное описание Вводной лекции...")


@dp.callback_query_handler(lambda c: c.data == 'minicourse_lectures')
async def process_minicourse_sub_category(call: types.CallbackQuery):
    await call.answer("Вы выбрали мини-курс.")  # подтверждение выбора
    await bot.send_message(call.message.chat.id,
                           "Полное описание 'Запись курса лекций по закупкам товаров в Китае без обратной связи 6888 "
                           "руб'...")


@dp.message_handler(lambda message: message.text.startswith('/'), state="*")
async def unknown_command(message: types.Message, state: FSMContext):
    await message.reply("Извини, я не понимаю эту команду. Я же просто бот. "
                        "Пожалуйста, используй одну из известных мне команд.",
                        reply_markup=main_menu_keyboard)
    await state.finish()  # Завершение FSM сессии


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
