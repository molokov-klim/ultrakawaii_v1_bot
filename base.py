import inspect

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
import config
from database import create_pool
from aiogram import types
from aiogram.utils import executor

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

main_menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.add("Главное меню")


class Base:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.pool = None

    async def on_startup(self, dp):
        try:
            self.pool = await create_pool()
        except Exception as error:
            pass

    def start_polling(self):
        try:
            executor.start_polling(dp, on_startup=self.on_startup, skip_updates=True)
        except Exception as error:
            pass
