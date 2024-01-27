from const.bot_text import BotText


class Services:
    callback = 'services'
    description = 'Услуги'

    class Agent:
        callback = 'agent'
        description = 'Агент'
        text = BotText.AGENT

    class Buying:
        callback = 'buying'
        description = 'Закупка'
        text = BotText.BUYING

    class Delivery:
        callback = 'delivery'
        description = 'Доставка'
        text = BotText.DELIVERY

    class Brand:
        callback = 'brand'
        description = 'Бренд'
        text = BotText.BRAND

    class Fulfillment:
        callback = 'fulfillment'
        description = 'Фулфилмент'
        text = BotText.FULFILLMENT

    list_services = [Agent, Buying, Delivery, Brand, Fulfillment]
