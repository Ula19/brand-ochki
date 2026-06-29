"""Временный модуль для теста Этапа 6 (обработка ошибок).

Команда /raise доступна только админу и намеренно вызывает исключение,
чтобы проверить, что глобальный errors-роутер ловит ошибку, пишет в лог
и уведомляет админа. После проверки этот файл можно удалить и убрать
import из main.py.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.filters.admin import IsAdmin

router = Router()
router.message.filter(IsAdmin())


@router.message(Command("raise"))
async def raise_for_test(message: Message) -> None:
    raise RuntimeError("Тест Этапа 6: исключение из /raise")
