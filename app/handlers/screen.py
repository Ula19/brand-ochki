"""Управление сообщениями текущего экрана каталога.

Лента товаров — это несколько фото-сообщений + панель управления. Их ID
хранятся в FSM, чтобы при любом переходе (листание, уход в меню, /start)
старый экран можно было удалить и не оставлять «хвосты» в чате.
"""
from aiogram import Bot
from aiogram.fsm.context import FSMContext

SCREEN_KEY = "screen_msg_ids"


async def clear_screen(bot: Bot, chat_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    for msg_id in data.get(SCREEN_KEY, []):
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    await state.update_data(**{SCREEN_KEY: []})


async def save_screen(state: FSMContext, msg_ids: list[int]) -> None:
    await state.update_data(**{SCREEN_KEY: msg_ids})
