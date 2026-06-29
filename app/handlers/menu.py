from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import queries
from app.handlers.screen import clear_screen
from app.keyboards import user as kb

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    await message.answer(
        "Добро пожаловать в магазин <b>Brand Ochki</b>!\n\nВыберите раздел:",
        reply_markup=kb.main_menu(_is_admin(message.from_user.id)),
    )


@router.message(F.text == kb.BTN_SHOP_INFO)
async def shop_info(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    text = await queries.get_setting(session, "shop_info", default=settings.shop_info)
    await message.answer(text)


@router.message(F.text == kb.BTN_CONTACTS)
async def contacts(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    text = await queries.get_setting(session, "contacts", default=settings.contacts)
    await message.answer(text)


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
