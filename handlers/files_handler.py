import inspect
import os
from datetime import datetime
import config


from aiogram import types
from aiogram.dispatcher import FSMContext
from FSM import Form

from database import get_user, get_all_users
from base import dp, bot, main_menu_keyboard
from base import Base
from handlers.registration_handler import process_email
base = Base()


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):

    try:
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
    except Exception as error:
        pass
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)

