from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import queries
from app.filters.admin import is_superadmin


class AdminUsernameMiddleware(BaseMiddleware):
    """Подтягивает актуальный @username добавленного админа в БД при каждом его заходе.

    Так супер-админу не нужно вручную узнавать username — в списке админов он
    появляется сам, как только админ что-то напишет боту. Запись в БД происходит
    только если username реально изменился.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        session: AsyncSession | None = data.get("session")
        if user is not None and session is not None and not is_superadmin(user.id):
            await queries.sync_admin_username(session, user.id, user.username or "")
        return await handler(event, data)
