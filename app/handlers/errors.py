import logging
import traceback
from html import escape

from aiogram import Bot, Router
from aiogram.types import ErrorEvent

from app.config import settings
from app.emojis import E

router = Router()
logger = logging.getLogger(__name__)

USER_MESSAGE = f"{E['warning']} Что-то пошло не так. Попробуйте позже или вернитесь в меню через /start."
TB_LIMIT = 3000  # Telegram режет сообщения > 4096


@router.errors()
async def on_error(event: ErrorEvent, bot: Bot) -> None:
    exc = event.exception
    update = event.update

    logger.exception("Unhandled exception in handler", exc_info=exc)

    chat_id: int | None = None
    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        if update.callback_query.message is not None:
            chat_id = update.callback_query.message.chat.id
        try:
            await update.callback_query.answer(
                "Что-то пошло не так. Попробуйте позже.",
                show_alert=True,
            )
        except Exception:
            logger.exception("Failed to answer callback query on error")

    if chat_id is not None and chat_id != settings.admin_id:
        try:
            await bot.send_message(chat_id, USER_MESSAGE)
        except Exception:
            logger.exception("Failed to notify user about error")

    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if len(tb) > TB_LIMIT:
        tb = "…\n" + tb[-TB_LIMIT:]
    try:
        await bot.send_message(
            settings.admin_id,
            f"{E['warning']} <b>Исключение в боте</b>\n\n<pre>{escape(tb)}</pre>",
        )
    except Exception:
        logger.exception("Failed to notify admin about error")
