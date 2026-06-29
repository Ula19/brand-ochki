from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import queries


def is_superadmin(user_id: int) -> bool:
    """Супер-админ — единственный из .env. Только он управляет другими админами."""
    return user_id == settings.admin_id


async def user_is_admin(session: AsyncSession, user_id: int) -> bool:
    """Доступ к админке: супер-админ из .env или добавленный им админ из БД."""
    return is_superadmin(user_id) or await queries.is_db_admin(session, user_id)


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        if event.from_user is None:
            return False
        return await user_is_admin(session, event.from_user.id)


class IsSuperAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if event.from_user is None:
            return False
        return is_superadmin(event.from_user.id)
