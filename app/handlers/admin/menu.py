from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.emojis import E
from app.filters.admin import is_superadmin
from app.handlers.screen import clear_screen
from app.keyboards import admin as akb
from app.keyboards import user as ukb

router = Router()

ADMIN_TITLE = f"{E['tools']} <b>Админ-панель</b>\n\nВыберите раздел:"


@router.message(F.text == ukb.BTN_ADMIN)
async def open_admin(message: Message, state: FSMContext, bot: Bot) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    await message.answer(
        ADMIN_TITLE,
        reply_markup=akb.admin_main(is_superadmin(message.from_user.id)),
    )


@router.callback_query(F.data == "admin:menu")
async def back_to_admin(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        ADMIN_TITLE,
        reply_markup=akb.admin_main(is_superadmin(callback.from_user.id)),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:close")
async def close_admin(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Выход из админки в обычное меню — чтобы посмотреть магазин глазами покупателя."""
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await bot.send_message(
        callback.message.chat.id,
        f"{E['home']} Главное меню:",
        reply_markup=ukb.main_menu(is_admin=True),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
async def cancel_fsm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        f"Действие отменено.\n\n{ADMIN_TITLE}",
        reply_markup=akb.admin_main(is_superadmin(callback.from_user.id)),
    )
    await callback.answer()
