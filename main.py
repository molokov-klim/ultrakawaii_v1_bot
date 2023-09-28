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
from database import create_pool, add_user, get_user, get_all_users

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
        types.InlineKeyboardButton("УСЛУГИ", callback_data='services'),
        # types.InlineKeyboardButton("Выкуп товара", callback_data='buy_goods'),
        types.InlineKeyboardButton("Консультация", callback_data='consultation'),
        types.InlineKeyboardButton("О нас", callback_data='about'),
        types.InlineKeyboardButton("Лекции", callback_data='lectures'),
    )

    # Отправка сообщения с кнопками
    await message.reply("Пожалуйста, выберите интересующий вас раздел:", reply_markup=markup)


# Обработчик выбора категории
@dp.callback_query_handler(lambda c: c.data in ['services', 'consultation', 'about', 'lectures'], state='*')
async def process_main_category(call: types.CallbackQuery, state: FSMContext):
    print(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("OK")  # подтверждение выбора
    await state.finish()  # завершение сессии бота

    # Отправка информационных сообщений в зависимости от выбранной категории
    if call.data == 'services':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("АГЕНТ", callback_data='agent'),
            types.InlineKeyboardButton("ВЫКУП", callback_data='buying'),
            types.InlineKeyboardButton("ДОСТАВКА", callback_data='delivery'),
            types.InlineKeyboardButton("БРЕНД", callback_data='brand'),
            types.InlineKeyboardButton("ФУЛФИЛМЕНТ", callback_data='fulfillment'),
        )
        await bot.send_message(call.message.chat.id, "Выберите подкатегорию:", reply_markup=markup)

    elif call.data == 'consultation':
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

''',
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'about':
        await bot.send_message(chat_id=call.message.chat.id, text=
f'''
Коммерческая компания Moanna Yiwu Trading Co. LTD
Мы находимся в городе Иу
Бизнес лицензия номер 91330782MA2M2F3W94 от 09.04.2021
''',
                               parse_mode=types.ParseMode.MARKDOWN)
        await bot.send_message(chat_id=call.message.chat.id,
                               text=
f'''
https://t.me/moanna_yiwu

https://instagram.com/ultra_kawaii
''',
                               parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'lectures':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Мини-курс \"Бизнес с Китаем для новичков\"",
                                       callback_data='mini_course_business_novice'),
            types.InlineKeyboardButton("Лекция \"Агент в Китае\"", callback_data='lecture_agent_in_china')
        )
        await bot.send_message(call.message.chat.id, "Выберите подкатегорию:", reply_markup=markup)


# services
@dp.callback_query_handler(
    lambda c: c.data in ['agent', 'buying', 'delivery', 'brand', 'fulfillment'])
async def process_services_sub_category(call: types.CallbackQuery):
    print(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("Вы выбрали подкатегорию.")  # подтверждение выбора

    if call.data == 'agent':
        await bot.send_message(call.message.chat.id,
                               text='''
Вы хотите начать закупать товары в Китае, чтобы усилить конкурентное преимущество своего бизнеса? Мы поможем сделать этот процесс простым и эффективным.

Мы обеспечим легкое решение для вашего бизнеса:

Вы можете мучительно заниматься поиском поставщиков в Китае и пытаться вести свои сделки самостоятельно, а можете доверить это нам. Китай - это совершенно другой мир и тут нужен особый подход. К тому же без знания китайского языка очень сложно работать с китайскими поставщиками. Также если у вас нет представительства в Китае, то вам будет очень сложно контролировать процессы.

Мы предлагаем вам идеальное решение - мы полностью берем на себя проведение всех этапов сделки, включая юридическое сопровождение, проверку поставщиков, контроль производства заказа - все шаги от поиска поставщика до отгрузки товара и доставки на Ваш склад.


Как это работает?

1. Расскажите нам о вашем бизнесе и товарах, которые вы хотите закупать в Китае

2. Мы исследуем рынок, найдем поставщиков, проверим и выберем подходящих и надежных

3. Мы проведем переговоры с поставщиками о ценах, условиях доставки и других деталях сделки

4. Заключим контракт с поставщиком от имени нашей компании в Китае, что обеспечивает безопасность сделки

5. Мы проконтролируем процесс производства, сроки и качество продукции

6. Поможем оптимального маршрута и способа доставки товаров от производителя до вашего склада


Почему выбирают нас?

- Опыт работы с китайским рынком более 15 лет
- 100% надежность и конфиденциальность
- С нами размещать заказы китайским поставщикам легко и эффективно



Для того, чтобы начать работу по закупкам заполните форму и отправьте обратно:

Форма запроса
https://disk.yandex.ru/i/7yUVeM8K1XVjKQ
        ''')
    elif call.data == 'buying':
        await bot.send_message(chat_id=call.message.chat.id, text=
        f'''
Также у нас есть услуга по выкупу товара по вашим ссылкам

Если вы уже нашли поставщика, но боитесь закупать у него самостоятельно и вам нужна помощь агента в сопровождении сделки под ключ, то в этом мы также можем вам помочь.
Для этого необходимо заполнить простую форму запроса, мы свяжемся с поставщиком и организуем закупку товара.

Как происходит процесс:
- мы оформляем заказ от имени китайской компании
-производим оплату поставщику
-принимаем товар на консолидационном складе, делаем вам фото и видео товара при необходимости
-упаковываем
-отправляем выбранным вами способом
Мы берем процент в зависимости от сложности исполнения заказа и его объема

Заполните форму для оформления заказа:
 ФОРМА ЗАПРОСА НА ВЫКУП ТОВАРА
https://disk.yandex.ru/i/qg9xvXWpmohSVw
 
Либо напишите сюда информацию по заказу и прикрепите ссылку 
        ''',
                               parse_mode=types.ParseMode.MARKDOWN)
    elif call.data == 'delivery':
        await bot.send_message(call.message.chat.id,
                               text='''
Мы предлагаем полный спектр услуг: от консолидации груза на складе и доставки, до представления интересов на таможне

- Многообразие вариантов доставки: Воздушная, морская, железнодорожная, мультимодальная перевозка — выбирайте оптимальный маршрут для вашего бизнеса
 
- Консолидация грузов на собственном складе в Китае - что обеспечивает сохранность вашего груза и исключит ошибки в отгрузке
 
- Таможенное Оформление: Мы берём на себя всю бумажную работу с документами (которую вы так сильно не любите), обеспечивая быстрый оформление таможенных процедур
 
- Дверь-в-Дверь: Предлагаем полный комплекс услуг по доставке от вашего поставщика до вашего склада
          
 Алгоритм действий
 
1. Предварительная расчет: отправьте нам информацию о вашем грузе для первичной консультации и расчета доставки и таможенных платежей
 
2. Подтверждение деталей: после согласования всех условий, мы начнем подготовку к отправке груза
3. Мы проконтролируем отгрузку и вам не нужно будет беспокоиться об этом
Подготовка пакета документов: мы подготовим и проверим все необходимые документы для таможенного оформления.
4. Представление ваших интересов на таможне: наши специалисты возьмут на себя представление груза и документов на таможенном посту. После успешного прохождения, груз будет готов к дальнейшей транспортировке или получению.
5. Доставка и приём груза: груз будет доставлен в указанное место в установленные сроки. Вы всегда будете знать где находится ваш груз
          
Почему выбрать нас?
 
- Большой опыт в таможенном оформлении
- Профессиональная команда специалистов по таможенному оформлению
 
С нами доставка и таможенное оформление грузов из Китая будет легким и быстрым!
        ''')
    elif call.data == 'brand':
        await bot.send_message(call.message.chat.id, text='''
Производство Товаров Под Вашим Брендом

Мы поможем вам осуществить вашу мечту - создать продукт под вашим брендом!
 
Мы полностью берем на себя весь процесс - от идеи до воплощения.
Наша опытная команда разработает дизайн упаковки, учитывая позиционирование вашего бренда,  ваши пожелания, а также соответствия требованиям маркетплейса.
  
Мы сами занимаемся поиском и отбором надежных поставщиков. Мы адаптируемся к вашим нуждам и возможностям, предлагая гибкие сроки и условия производства.
 
СТРОГАЯ КОНФИДЕНЦИАЛЬНОСТЬ:
Ваши идеи и бренд находятся в безопасности, благодаря строгим мерам конфиденциальности, которые мы принимаем, чтобы защитить ваш продукт.
 
1. Консультация и Планирование: Мы обсуждаем с вами все детали — от выбора материалов до дизайнерских решений.
 
2. Проектирование и создание образца прототипа: Прежде чем начать производство, мы создаем прототип (мастер сэмпл)  для подтверждения при необходимости.
 
3. Производство: после утверждения прототипа, начинается массовое производство.
 
4. Контроль качества и доставка: партия проходит контроль качества перед отгрузкой.
 
5. Вы получаете продукт под вашим брендом
 
Создайте продукт, которым вы будете гордиться, вместе с нами!
        ''')
    elif call.data == 'fulfillment':
        await bot.send_message(call.message.chat.id, text='''
Если вы заказываете небольшие партии товара с 1688 и вам до смерти надоело заниматься переупаковкой товара самим, переложить это дело на плечи поставщика не позволяют минимальное количество заказа фабрики.
Если вы хотите освободить себя от этой бесконечной работы кладовщика, и вам надоел склад дома, то мы можем предложить вам услуги фулфилмента в Китае.

Представьте, что весь товар будет приходить к вам полностью готовый под отгрузку на вайлдбериз. Больше никакой стикеровки, больше никакой отбраковки без возможности вернуть неликвидный товар.

Всё можно переупаковать прямо на складе в Китае, проверить товар по вашему ТЗ, нанести штрих-код этикетки для wb и ozon.

Товар приходит к вам упакованный в красивую упаковку (без иероглифов), простикерованный и вам остаётся только отгрузить на склады маркетплейсов.

Что мы предлагаем:

выкуп с 1688
фулфилмент (QC и переупаковка)
доставка в РФ

Условия:

комиссия в зависимости от стоимости партии

небольшие минимальные количества заказа

надежная доставка с гарантией

заказ пробной партии товара

тестирование образцов

Мы берём на себя все сложности, связанные с заказом товара в Китае.

Также у нас есть производство фирменной упаковки - профессиональный дизайн в подарок

Если вам интересна данная услуга, то просто напишите в ответ:
        ''')

# lectures
@dp.callback_query_handler(
    lambda c: c.data in ['mini_course_business_novice', 'lecture_agent_in_china'])
async def process_lectures_sub_category(call: types.CallbackQuery):
    print(f"{inspect.currentframe().f_code.co_name}")
    await call.answer("Вы выбрали подкатегорию.")  # подтверждение выбора

    if call.data == 'mini_course_business_novice':
        await bot.send_message(call.message.chat.id, text='''
описание курса и ссылка на оплату
        ''')
        await bot.send_message(call.message.chat.id, text='''
записаться
                ''')

    elif call.data == 'lecture_agent_in_china':
        await bot.send_message(call.message.chat.id, text=f'''
{config.INTRO_LECTURE}
        ''')


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
    except:
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
    print(f"{inspect.currentframe().f_code.co_name}")
    print("del")

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
        await message.reply(f"Вы не администратор", reply_markup=main_menu_keyboard)


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
