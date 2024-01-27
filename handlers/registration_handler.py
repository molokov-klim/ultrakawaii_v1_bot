import inspect
from aiogram import types

from aiogram.dispatcher import FSMContext
from email_validator import EmailNotValidError, validate_email

from FSM import Form
from base import dp, bot, main_menu_keyboard
from database import add_user
from base import Base


base = Base()


# Обработчик ввода email
@dp.message_handler(state=Form.email, content_types=types.ContentTypes.TEXT)
async def process_email(message: types.Message, state: FSMContext):
    
    try:
        await message.reply("Проверяю email")
        pool = base.pool
        email = message.text
        try:
            # Валидация email
            v = validate_email(email)
            valid_email = v.email
        except EmailNotValidError:
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
    except Exception as error:
        pass
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)
