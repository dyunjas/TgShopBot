import asyncio

from backend.core.loader import (
    setup_bot,
    shutdown_bot
)

from backend.database.session import (
    init_db,
    check_connection,
    engine
)

from backend.middlewares.db import DBSessionMiddleware
from backend.middlewares.user_update import UserUpdateMiddleware

from bot.admin import admin_routers
from bot import bot_routers

from backend.core.logger_config import logger

async def main():
    try:

        bot, dp = await setup_bot()

        await init_db()
        await check_connection()

        dp.update.middleware(DBSessionMiddleware())
        dp.update.middleware(UserUpdateMiddleware())

        dp.include_router(admin_routers.router)
        dp.include_router(bot_routers.router)

        await bot.delete_webhook(drop_pending_updates=True)

        logger.info("Bot started")
        await dp.start_polling(bot)

    except Exception as e:
        logger.exception(f"Bot crashed {e}")
    finally:
        await shutdown_bot(bot)
        await engine.dispose()
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())