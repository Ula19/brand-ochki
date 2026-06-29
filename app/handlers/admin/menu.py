from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.filters.admin import is_superadmin
from app.handlers.screen import clear_screen
from app.keyboards import admin as akb
from app.keyboards import user as ukb

router = Router()


@router.message(F.text == ukb.BTN_ADMIN)
async def open_admin(message: Message, state: FSMContext, bot: Bot) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
        reply_markup=akb.admin_main(is_superadmin(message.from_user.id)),
    )


@router.callback_query(F.data == "admin:menu")
async def back_to_admin(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
        reply_markup=akb.admin_main(is_superadmin(callback.from_user.id)),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
async def cancel_fsm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Действие отменено.\n\n🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
        reply_markup=akb.admin_main(is_superadmin(callback.from_user.id)),
    )
    await callback.answer()
