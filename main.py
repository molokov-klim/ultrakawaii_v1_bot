import inspect
import logging
import os.path
import time
from datetime import datetime

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
    print(f"{inspect.currentframe().f_code.co_name}")
    global pool
    pool = await create_pool()


# Определение состояний для машины состояний
class Form(StatesGroup):
    email = State()  # состояние для email
    category = State()  # состояние для категории


# Обработчик команды /start
@dp.message_handler(commands='start', state='*')
async def cmd_start(message: types.Message):
    print(f"{inspect.currentframe().f_code.co_name}")
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
    print(f"{inspect.currentframe().f_code.co_name}")
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
    print(f"{inspect.currentframe().f_code.co_name}")
    # Создание кнопок для выбора категории
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Мои услуги", callback_data='services'),
        types.InlineKeyboardButton("Выкуп товара", callback_data='buy_goods'),
        types.InlineKeyboardButton("Консультация", callback_data='training'),
        types.InlineKeyboardButton("Полезное", callback_data='useful'),
        types.InlineKeyboardButton("Подарочки", callback_data='gifts'),
    )

    # Отправка сообщения с кнопками
    await message.reply("Пожалуйста, выберите интересующий вас раздел:", reply_markup=markup)


# Обработчик выбора категории
@dp.callback_query_handler(lambda c: c.data in ['services', 'buy_goods', 'training', 'useful', 'gifts'], state='*')
async def process_main_category(call: types.CallbackQuery, state: FSMContext):
    print(f"{inspect.currentframe().f_code.co_name}")
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

    elif call.data == 'buy_goods':
        await bot.send_message(chat_id=call.message.chat.id, text=
        f'''
                Если вы уже нашли поставщика, но боитесь закупать у него самостоятельно и вам нужна помощь агента в сопровождении сделки под ключ, то в этом мы также можем вам помочь.
                Для этого необходимо заполнить простую форму запроса, *мы свяжемся с поставщиком и организуем закупку товара*.
                
                Как происходит процесс: 
                - мы оформляем заказ от имени китайской компании
                - производим оплату поставщику
                - принимаем товар на консолидационном складе, делаем вам фото и видео товара при необходимости
                - упаковываем
                - отправляем выбранным вами способом
                Мы берем процент в зависимости от сложности исполнения заказа и его объема
                
                Для оформления заказа *заполните форму и отправьте* мне.:
                👇👇👇
                
                {config.BUY_GOODS_FORM}
                ''',
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'training':
        await bot.send_message(chat_id=call.message.chat.id, text=
        f'''
        *Консультация по закупкам товаров из Китая*

        *Кому подходит:*
        Тем кто хочет начать работать с Китаем, но не знает с чего начать и куда двигаться
        
        *Формат:*
        Персональная консультация в зуме длительностью 3-4 часа
        После консультации у вас будет запись и файл с рекомендациями
        
        *План работ:*
        Вы приходите со списком товаров, которые хотели бы закупать. Мы с вами вместе проанализируем и посчитаем будет ли выгодно их начинать закупать.
        
        Посчитаем таргет прайс (по какой цене выгодно будет закупать товар), а также какой бюджет нужен для закупки первой партии товара, а также какое количество товара вам нужно закупить для старта.
        
        - Найдем поставщиков и проверим цены. 
        
        - Продумаем вашу упаковку и посчитаем примерную стоимость.
        
        - Посчитаем стоимость доставки 
        
        + Рассмотрим всю схему взаимодействия с китайскими поставщиками, как заказывать, как везти товар и т.д.
        Что делать в случае брака, как избежать брака
        
        Следующий созвон через три дня и мы обсуждаем ваши оставшиеся вопросы. После этого неделя обратной связи в телеграмме.
        
        *Стоимость 28888 руб*
        *Записаться: @ultra_kawaii*
        ''',
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'useful':
        await bot.send_message(chat_id=call.message.chat.id,
                               text=
                               f'''
                               https://t.me/moanna_yiwu
                        
                               https://instagram.com/ultra_kawaii
                               ''',
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'gifts':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Рабочая тетрадь какой товар везти из Китая", callback_data='workbook'),
            types.InlineKeyboardButton("Вводная лекция", callback_data='intro_lecture')
        )
        await bot.send_message(call.message.chat.id, "Выберите подарок:", reply_markup=markup)


@dp.callback_query_handler(
    lambda c: c.data in ['find_suppliers', 'purchase_agent', 'factory_check', 'customs', 'turnkey_brand'])
async def process_services_sub_category(call: types.CallbackQuery):
    print(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("Вы выбрали подкатегорию.")  # подтверждение выбора

    if call.data == 'find_suppliers':
        await bot.send_message(call.message.chat.id, "Форма и описание для поиска поставщиков и товаров. В разработке.")
    elif call.data == 'purchase_agent':
        await bot.send_message(chat_id=call.message.chat.id, text=
        f'''
        Как агент по закупкам в Китае, я могу предоставить вам следующие услуги, направленные на облегчение процесса закупки товаров и услуг от китайских производителей и поставщиков:

        1. *Поиск* надёжных производителей или поставщиков
        2. *Мы проводим переговоры* о ценах, условиях доставки и других деталях сделки
        3. *Контроль качества* продукции на различных этапах производства
        4. *Логистика*: выбор оптимального маршрута и способа доставки товаров от производителя до вашего склада
        5. *Документация*: Помощь в оформлении всех необходимых таможенных и экспортных документов
        6. *Бренд под ключ* - мы полностью берем на себя всю работу по созданию товара под вашим брендом
        
        Мой сервис особенно полезен для компаний, не имеющих опыта работы с китайскими рынками или желающих сэкономить время и ресурсы.
        
        Для начала работы со мной, *заполните форму и отправьте* мне.
        👇👇👇
        
        {config.REQUEST_FORM}
        ''',
                               parse_mode=types.ParseMode.MARKDOWN)
    elif call.data == 'factory_check':
        await bot.send_message(call.message.chat.id, "Описание проверки фабрики. В разработке.")
    elif call.data == 'customs':
        await bot.send_message(call.message.chat.id, "Описание доставки и таможенного оформления. В разработке.")
    elif call.data == 'turnkey_brand':
        await bot.send_message(call.message.chat.id, "Описание услуги 'Бренд под ключ'. В разработке.")


@dp.callback_query_handler(
    lambda c: c.data in ['express_consultation', 'personal_session', 'big_consultation', 'mentorship'])
async def process_training_sub_category(call: types.CallbackQuery):
    print(f"{inspect.currentframe().f_code.co_name}")
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
    print(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("Вы выбрали подарок.")  # подтверждение выбора

    if call.data == 'workbook':
        await bot.send_message(call.message.chat.id, "Скоро будет добавлена")
    elif call.data == 'intro_lecture':
        await bot.send_message(call.message.chat.id, f"{config.INTRO_LECTURE}")


@dp.callback_query_handler(lambda c: c.data == 'minicourse_lectures')
async def process_minicourse_sub_category(call: types.CallbackQuery):
    print(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("Вы выбрали мини-курс.")  # подтверждение выбора
    await bot.send_message(call.message.chat.id,
                           "Полное описание 'Запись курса лекций по закупкам товаров в Китае без обратной связи 6888 "
                           "руб'...")


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    print(f"{inspect.currentframe().f_code.co_name}")
    file_id = message.document.file_id
    file_name = message.document.file_name

    if '.xls' not in str(file_name) and '.xlsx' not in str(file_name):
        await message.reply(
            f"Документ не принят. Пожалуйста используйте формат .xls или .xlsx")
        return
    await message.reply(
        f"Документ принят. Он будет передан нашей команде в обработку. Мы с вами свяжемся в ближайшее время")

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
    except:
        pass

    user_mention = f"@{username}"
    user_id = message.from_user.id  # Получение user_id из сообщения

    async with pool.acquire() as conn:
        user_data = await get_user(conn, user_id)

    await bot.send_message(chat_id=config.ADMIN_ID, text=f'''
    Принят документ от {message.from_user.first_name} {message.from_user.last_name}
    username: {user_mention}
    email: {user_data['email']}
    ''')
    await bot.send_document(chat_id=config.ADMIN_ID, document=file_id)
    await bot.send_message(chat_id=config.ADMIN_2_ID, text=f'''
    Принят документ от {message.from_user.first_name} {message.from_user.last_name}
    username: {user_mention}
    email: {user_data['email']}
    ''')
    await bot.send_document(chat_id=config.ADMIN_2_ID, document=file_id)


@dp.message_handler(lambda message: message.text.startswith('/'), state="*")
async def unknown_command(message: types.Message, state: FSMContext):
    print(f"{inspect.currentframe().f_code.co_name}")
    await message.reply("Извини, я не понимаю эту команду. Я же просто бот. "
                        "Пожалуйста, используй одну из известных мне команд.",
                        reply_markup=main_menu_keyboard)
    await state.finish()  # Завершение FSM сессии


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
