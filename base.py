import inspect

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from loguru import logger
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
        logger.info(f"{inspect.currentframe().f_code.co_name}")
        if not cls._instance:
            logger.info(f"{inspect.currentframe().f_code.co_name}")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        logger.info(f"{inspect.currentframe().f_code.co_name}")
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.pool = None

    async def on_startup(self, dp):
        logger.info(f"{inspect.currentframe().f_code.co_name}")
        self.pool = await create_pool()

    def start_polling(self):
        logger.info(f"{inspect.currentframe().f_code.co_name}")
        executor.start_polling(dp, on_startup=self.on_startup, skip_updates=True)


