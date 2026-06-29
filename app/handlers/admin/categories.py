from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import queries
from app.emojis import E
from app.keyboards import admin as akb
from app.states.admin import AddCategory

router = Router()


async def _show_list(message: Message, session: AsyncSession, *, edit: bool, prefix: str = "") -> None:
    cats = await queries.list_all_categories(session)
    header = f"{E['folder']} <b>Категории</b>\n\nНажмите на категорию, чтобы активировать/деактивировать."
    text = f"{prefix}{header}" if prefix else header
    if edit:
        await message.edit_text(text, reply_markup=akb.categories_admin(cats))
    else:
        await message.answer(text, reply_markup=akb.categories_admin(cats))


@router.callback_query(F.data == "admin:c:list")
async def list_categories(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_list(callback.message, session, edit=True)
    await callback.answer()


@router.callback_query(F.data == "admin:c:add")
async def start_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddCategory.waiting_name)
    await callback.message.edit_text(
        "Введите название новой категории (до 100 символов):",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(AddCategory.waiting_name, F.text)
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
        await queries.create_category(session, name)
    except IntegrityError:
        await session.rollback()
        await message.answer(
            f"Категория «{name}» уже существует. Введите другое название:",
            reply_markup=akb.cancel_kb(),
        )
        return
    await state.clear()
    await _show_list(message, session, edit=False, prefix=f"{E['check']} Категория «{name}» добавлена.\n\n")


@router.callback_query(F.data.startswith("admin:c:toggle:"))
async def toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    cat_id = int(callback.data.rsplit(":", 1)[1])
    new_state = await queries.toggle_category(session, cat_id)
    if new_state is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    cats = await queries.list_all_categories(session)
    await callback.message.edit_reply_markup(reply_markup=akb.categories_admin(cats))
    await callback.answer("Активирована." if new_state else "Деактивирована.")
