import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from database import init_db
from handlers import setup_routers
from middlewares import CheckBlockMiddleware
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)


async def main():
    await init_db()

    # Включаем HTML-разметку по умолчанию
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.message.middleware(CheckBlockMiddleware())
    dp.callback_query.middleware(CheckBlockMiddleware())

    dp.include_router(setup_routers())
    setup_scheduler(bot)

    print("Бот запущен и готов к работе!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())