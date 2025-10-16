from aiogram import Bot, Dispatcher
import asyncio
import os
from dotenv import load_dotenv
import logging
from app.handlers import router
from app.admin_panel import admin_router

load_dotenv()

token = os.getenv("BOT_TOKEN")

async def main(token):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - [%(levelname)s] - '  # логирование нужно для отображения результата работы хендлера: is handled / is not handled
                               '%(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')

    bot = Bot(token)
    dp = Dispatcher()

    dp.include_router(router)
    dp.include_router(admin_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main(token=token))
    