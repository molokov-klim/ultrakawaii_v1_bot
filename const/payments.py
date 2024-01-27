class Payments:
    description = 'Оплата'
    callback = 'payments'

    class TestPayment:
        description = 'Тестовая оплата'
        callback = 'test_payment'
        text = 'Текст по оплате'
        image = 'https://5f32cfce-80a7-4ffa-a97f-34e3134a7fe2.selstorage.ru/trash/money.png'
        prices = [{
            "label": "Руб.",
            "amount": 15000
        }]
        payload = 'test_payment_payload'
        start_parameter = "start_parameter_test_payment"
