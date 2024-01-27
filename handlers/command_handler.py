import inspect

import config

from aiogram import types
from aiogram.dispatcher import FSMContext
from FSM import Form

from database import get_user, get_all_users
from base import dp, bot, main_menu_keyboard
from base import Base
from handlers.registration_handler import process_email

base = Base()


# Обработчик команды /start
@dp.message_handler(commands='start', state='*')
async def start(message: types.Message):
    
    try:
        pool = base.pool
        user_id = message.from_user.id  # Получение user_id из сообщения

        async with pool.acquire() as conn:
            user_data = await get_user(conn, user_id)

        if user_data:
            await message.reply(f"Здравствуй, {message.from_user.first_name}!", reply_markup=main_menu_keyboard)
        else:
            await Form.email.set()  # переход к состоянию имени
            await message.reply(
                f"Здравствуй, {message.from_user.first_name}! Напиши свой email для окончания регистрации.")  # отправка сообщения
    except Exception as error:
        pass
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)


@dp.message_handler(commands='admin', state="*")
async def admin(message: types.Message, state: FSMContext):
    
    try:
        pool = base.pool
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
    except Exception as error:
        pass
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)
