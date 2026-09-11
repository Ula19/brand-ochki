from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import queries
from app.filters.admin import user_is_admin
from app.handlers.screen import clear_screen, save_screen
from app.keyboards import user as kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    is_admin = await user_is_admin(session, message.from_user.id)
    await message.answer(
        "Добро пожаловать в магазин <b>Brand Ochki</b>!\n\nВыберите раздел:",
        reply_markup=kb.main_menu(is_admin),
    )


async def _show_info(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot, key: str, default: str
) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    text = await queries.get_setting(session, key, default=default)
    m = await message.answer(text, reply_markup=kb.to_menu_kb())
    await save_screen(state, [m.message_id])


@router.message(F.text == kb.BTN_SHOP_INFO)
async def shop_info(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await _show_info(message, state, session, bot, "shop_info", settings.shop_info)


@router.message(F.text == kb.BTN_CONTACTS)
async def contacts(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await _show_info(message, state, session, bot, "contacts", settings.contacts)


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
