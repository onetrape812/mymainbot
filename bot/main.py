import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database.engine import init_db
from bot.middlewares.db import DatabaseMiddleware

from bot.handlers import start, portfolio, reviews, feedback, contact, admin, admin_portfolio, post_builder


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger = logging.getLogger(__name__)

    await init_db()
    logger.info("Database initialized.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    dp.include_routers(
        admin.router,
        admin_portfolio.router,
        post_builder.router,
        start.router,
        portfolio.router,
        reviews.router,
        feedback.router,
        contact.router,
    )

    logger.info("Bot started. Listening for updates...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
