from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from app.config import settings


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if event.from_user is None:
            return False
        return event.from_user.id == settings.admin_id
