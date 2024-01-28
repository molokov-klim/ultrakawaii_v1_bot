import inspect
from aiogram import types

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from email_validator import EmailNotValidError, validate_email

import config
from FSM import Form
from base import dp, bot, main_menu_keyboard
from const.payments import Payments
from database import add_user
from base import Base


base = Base()


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



