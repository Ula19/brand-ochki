from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import queries
from app.emojis import E
from app.filters.admin import IsSuperAdmin
from app.keyboards import admin as akb
from app.states.admin import AddAdmin

router = Router()
# Весь раздел доступен только супер-админу (id из .env).
router.message.filter(IsSuperAdmin())
router.callback_query.filter(IsSuperAdmin())


async def _show_admins(message: Message, session: AsyncSession, *, edit: bool, prefix: str = "") -> None:
    admins = await queries.list_admins(session)
    if admins:
        header = f"{E['users']} <b>Админы</b>\n\nДобавленные админы. Нажмите, чтобы удалить."
    else:
        header = f"{E['users']} <b>Админы</b>\n\nПока никого не добавлено."
    text = f"{prefix}{header}" if prefix else header
    markup = akb.admins_admin(admins)
    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.callback_query(F.data == "admin:adm:list")
async def list_admins(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    await _show_admins(callback.message, session, edit=True)
    await callback.answer()


# ---------- Добавление ----------

@router.callback_query(F.data == "admin:adm:add")
async def add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddAdmin.waiting_id)
    await callback.message.edit_text(
        "Отправьте числовой Telegram ID нового админа.\n"
        "Узнать ID можно через @userinfobot.",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(AddAdmin.waiting_id, F.text)
async def add_receive(message: Message, state: FSMContext, session: AsyncSession) -> None:
    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer(
            "Это не похоже на числовой ID. Введите ещё раз:",
            reply_markup=akb.cancel_kb(),
        )
        return
    telegram_id = int(raw)
    if telegram_id == settings.admin_id:
        await message.answer(
            "Это супер-админ — у него и так полный доступ. Введите другой ID:",
            reply_markup=akb.cancel_kb(),
        )
        return
    if await queries.is_db_admin(session, telegram_id):
        await message.answer(
            "Этот пользователь уже админ. Введите другой ID или нажмите «Отмена».",
            reply_markup=akb.cancel_kb(),
        )
        return
    try:
        await queries.add_admin(session, telegram_id, "", message.from_user.id)
    except IntegrityError:
        await session.rollback()
        await message.answer(
            "Этот пользователь уже админ.",
            reply_markup=akb.cancel_kb(),
        )
        return
    await state.clear()
    await _show_admins(session=session, message=message, edit=False, prefix=f"{E['check']} Админ (ID {telegram_id}) добавлен.\n\n")


# ---------- Удаление (с подтверждением) ----------

@router.callback_query(F.data.startswith("admin:adm:del:"))
async def del_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_id = int(callback.data.rsplit(":", 1)[1])
    admin = await queries.get_admin(session, telegram_id)
    if admin is None:
        await callback.answer("Админ не найден", show_alert=True)
        return
    label = f"@{admin.username}" if admin.username else f"ID {admin.telegram_id}"
    await callback.message.edit_text(
        f"Удалить админа {label}? Он потеряет доступ к админ-панели.",
        reply_markup=akb.confirm_remove_admin(telegram_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:adm:rm:"))
async def del_do(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_id = int(callback.data.rsplit(":", 1)[1])
    removed = await queries.remove_admin(session, telegram_id)
    await _show_admins(callback.message, session, edit=True)
    await callback.answer("Админ удалён." if removed else "Админ не найден.")
