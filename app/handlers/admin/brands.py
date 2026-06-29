from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import queries
from app.keyboards import admin as akb
from app.states.admin import AddBrand

router = Router()


async def _show_list(message: Message, session: AsyncSession, prefix: str = "") -> None:
    brands = await queries.list_all_brands(session)
    header = "🏷 <b>Бренды</b>\n\nНажмите на бренд, чтобы активировать/деактивировать."
    text = f"{prefix}{header}" if prefix else header
    if message.text is not None:
        await message.edit_text(text, reply_markup=akb.brands_admin(brands))
    else:
        await message.answer(text, reply_markup=akb.brands_admin(brands))


@router.callback_query(F.data == "admin:b:list")
async def list_brands(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_list(callback.message, session)
    await callback.answer()


@router.callback_query(F.data == "admin:b:add")
async def start_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddBrand.waiting_name)
    await callback.message.edit_text(
        "Введите название нового бренда (до 100 символов):",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(AddBrand.waiting_name, F.text)
async def receive_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("Пустое название, введите ещё раз:", reply_markup=akb.cancel_kb())
        return
    if len(name) > 100:
        await message.answer(
            "Слишком длинное название (максимум 100 символов). Попробуйте ещё раз:",
            reply_markup=akb.cancel_kb(),
        )
        return
    try:
        await queries.create_brand(session, name)
    except IntegrityError:
        await session.rollback()
        await message.answer(
            f"Бренд «{name}» уже существует. Введите другое название:",
            reply_markup=akb.cancel_kb(),
        )
        return
    await state.clear()
    await _show_list(message, session, prefix=f"✅ Бренд «{name}» добавлен.\n\n")


@router.callback_query(F.data.startswith("admin:b:toggle:"))
async def toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    brand_id = int(callback.data.rsplit(":", 1)[1])
    new_state = await queries.toggle_brand(session, brand_id)
    if new_state is None:
        await callback.answer("Бренд не найден", show_alert=True)
        return
    brands = await queries.list_all_brands(session)
    await callback.message.edit_reply_markup(reply_markup=akb.brands_admin(brands))
    await callback.answer("Активирован." if new_state else "Деактивирован.")
