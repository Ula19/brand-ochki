import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database.base import async_session_maker
from app.handlers import catalog, debug, errors, menu
from app.handlers.admin import admin_router
from app.logging_config import setup_logging
from app.middlewares.admin_sync import AdminUsernameMiddleware
from app.middlewares.database import DatabaseMiddleware


async def main() -> None:
    setup_logging()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DatabaseMiddleware(async_session_maker))
    dp.update.middleware(AdminUsernameMiddleware())

    # Errors-роутер подключаем первым, чтобы он ловил всё.
    dp.include_router(errors.router)
    dp.include_router(menu.router)
    dp.include_router(catalog.router)
    dp.include_router(admin_router)
    dp.include_router(debug.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
