import asyncio
import threading
from time import sleep
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Dispatcher, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

from databases.database import Database
from start_for_webdriver.webdriver import webdriver
from start_for_webdriver.login_in_twitter import login_in_twitter
from config import Config, load_config
from handlers import admin_handlers, user_handlers

async def main(load_config):
    storage: MemoryStorage = MemoryStorage()
    config = load_config()
    dp = Dispatcher(storage=storage)
    bot = Bot(token=config.tg_bot.token, parse_mode="HTML")

    # dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main(load_config))



