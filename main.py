import inspect
import os.path
from datetime import datetime

from aiogram.types import ContentType
from email_validator import validate_email, EmailNotValidError

from aiogram import types

from aiogram.dispatcher import FSMContext

# from aiogram.utils import executor

from FSM import Form

from database import create_pool, add_user, get_user, get_all_users
from const.lectures import Lectures
from const.services import Services
from const.consultation import Consultation
from const.about import About
from const.payments import Payments

import config

from base import dp, bot, main_menu_keyboard
from base import Base
from handlers.command_handler import start, admin
from handlers.files_handler import handle_docs
from handlers.registration_handler import process_email
from handlers.other_handlers import unknown_command

base = Base()


@dp.message_handler(lambda message: message.text == "Главное меню")
async def show_main_menu(message: types.Message):
    try:

        # Создание кнопок для выбора категории
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(text=Services.description, callback_data=Services.callback),
            types.InlineKeyboardButton(text=Consultation.description, callback_data=Consultation.callback),
            types.InlineKeyboardButton(text=Lectures.description, callback_data=Lectures.callback),
            types.InlineKeyboardButton(text=About.description, callback_data=About.callback),
            types.InlineKeyboardButton(text=Payments.description, callback_data=Payments.callback)
        )

        # Отправка сообщения с кнопками
        await message.reply("Пожалуйста, выберите интересующий вас раздел:", reply_markup=markup)
    except Exception as error:
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)
        pass


# Обработчик выбора категории
@dp.callback_query_handler(lambda c: c.data in [
    Services.callback,
    Consultation.callback,
    About.callback,
    Lectures.callback,
    Payments.callback], state='*')
async def process_main_category(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.answer("")  # подтверждение выбора
        await state.finish()  # завершение сессии бота

        # Отправка информационных сообщений в зависимости от выбранной категории
        if call.data == Services.callback:
            markup = types.InlineKeyboardMarkup()
            for service in Services.list_services:
                markup.add(types.InlineKeyboardButton(text=service.description,
                                                      callback_data=service.callback))
            await bot.send_message(call.message.chat.id, "Выберите услугу:", reply_markup=markup)

        elif call.data == Consultation.callback:
            await bot.send_message(chat_id=call.message.chat.id, text=Consultation.text,
                                   parse_mode=types.ParseMode.MARKDOWN)

        elif call.data == About.callback:
            await bot.send_message(chat_id=call.message.chat.id, text=About.text,
                                   parse_mode=types.ParseMode.MARKDOWN)

        elif call.data == Lectures.callback:
            markup = types.InlineKeyboardMarkup()
            for lecture in Lectures.list_lectures:
                markup.add(types.InlineKeyboardButton(text=lecture.description,
                                                      callback_data=lecture.callback))
            await bot.send_message(call.message.chat.id, "Выберите лекцию:", reply_markup=markup)

        elif call.data == Payments.callback:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text=Payments.TestPayment.description,
                                                  callback_data=Payments.TestPayment.callback))
            await bot.send_message(call.message.chat.id, "Выберите оплату:", reply_markup=markup)

    except Exception as error:
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)
        pass


@dp.callback_query_handler(
    lambda c: any(c.data == service.callback for service in Services.list_services)
)
async def process_services_sub_category(call: types.CallbackQuery):
    try:
        await call.answer("")  # подтверждение выбора
        for service in Services.list_services:
            if call.data == service.callback:
                await bot.send_message(call.message.chat.id, text=service.text)
    except Exception as error:
        await bot.send_message("Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)
        pass


# lectures
@dp.callback_query_handler(
    lambda c: any(c.data == lecture.callback for lecture in Lectures.list_lectures)
)
async def process_lectures_sub_category(call: types.CallbackQuery):
    try:
        await call.answer("")  # подтверждение выбора
        for lecture in Lectures.list_lectures:
            if call.data == lecture.callback:
                await bot.send_message(call.message.chat.id, text=lecture.link)
    except Exception as error:
        await bot.send_message(f"Что-то пошло не так. Повторите пожалуйста",
                               reply_markup=main_menu_keyboard)
        pass


@dp.callback_query_handler(text=Payments.TestPayment.callback)
async def test_payment(call: types.CallbackQuery):
    await bot.send_invoice(chat_id=call.from_user.id,
                           title=Payments.TestPayment.text,
                           description=Payments.TestPayment.description,
                           provider_token=config.YOUKASSA_TOKEN_TEST,
                           currency='rub',
                           photo_url=Payments.TestPayment.image,
                           photo_height=512,  # !=0/None, иначе изображение не покажется
                           photo_width=512,
                           photo_size=512,
                           is_flexible=False,  # True если конечная цена зависит от способа доставки
                           prices=Payments.TestPayment.prices,
                           start_parameter=Payments.TestPayment.start_parameter,
                           payload=Payments.TestPayment.payload
                           )


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
    if message.successful_payment.invoice_payload == 'test_payment_payload':
        await bot.send_message(message.from_user.id, "Оплата принята, спасибо")


# Запуск бота
if __name__ == '__main__':
    base.start_polling()
