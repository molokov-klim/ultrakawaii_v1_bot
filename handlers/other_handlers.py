import inspect
from aiogram import types

from aiogram.dispatcher import FSMContext
from email_validator import EmailNotValidError, validate_email

from FSM import Form
from base import dp, bot, main_menu_keyboard
from database import add_user
from base import Base

base = Base()


@dp.message_handler(lambda message: message.text.startswith('/'), state="*")
async def unknown_command(message: types.Message, state: FSMContext):
    
    try:
        await message.reply("Извините, я не понимаю эту команду. Я же просто бот. "
                            "Пожалуйста, используйте одну из известных мне команд.",
                            reply_markup=main_menu_keyboard)
        await state.finish()  # Завершение FSM сессии
    except Exception as error:
        pass
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)
