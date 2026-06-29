from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import queries
from app.emojis import E
from app.keyboards import admin as akb
from app.states.admin import EditSetting

router = Router()


# Ключ → (название, дефолт из .env, имя премиум-эмодзи). Дефолт — если в БД ещё пусто.
TEXTS = {
    "shop_info": ("О магазине", "shop_info", "pin"),
    "contacts": ("Контакты", "contacts", "phone"),
}


def _default_for(key: str) -> str:
    return getattr(settings, TEXTS[key][1])


def _label(key: str) -> str:
    """Название текста с премиум-иконкой для сообщений."""
    return f"{E[TEXTS[key][2]]} {TEXTS[key][0]}"


@router.callback_query(F.data == "admin:t:menu")
async def texts_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        f"{E['memo']} <b>Тексты</b>\n\nВыберите текст для просмотра и редактирования:",
        reply_markup=akb.texts_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:t:show:"))
async def show_text(callback: CallbackQuery, session: AsyncSession) -> None:
    key = callback.data.rsplit(":", 1)[1]
    if key not in TEXTS:
        await callback.answer("Неизвестный текст", show_alert=True)
        return
    current = await queries.get_setting(session, key, default=_default_for(key))
    await callback.message.edit_text(
        f"<b>{_label(key)}</b> — текущий текст:\n\n{current}",
        reply_markup=akb.text_show_kb(key),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:t:edit:"))
async def edit_text_start(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.rsplit(":", 1)[1]
    if key not in TEXTS:
        await callback.answer("Неизвестный текст", show_alert=True)
        return
    await state.set_state(EditSetting.waiting_value)
    await state.update_data(key=key)
    await callback.message.edit_text(
        f"Отправьте новый текст для «{_label(key)}».\n\n"
        "Можно использовать HTML: <b>жирный</b>, <i>курсив</i>, "
        "<a href='https://example.com'>ссылка</a>, <a href='tel:+998901234567'>номер</a>.\n"
        "Переносы строк сохраняются как есть.",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(EditSetting.waiting_value, F.text)
async def edit_text_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    key = data["key"]
    new_value = message.text.strip()
    if not new_value:
        await message.answer("Пустой текст. Введите ещё раз:", reply_markup=akb.cancel_kb())
        return
    if len(new_value) > 4000:
        await message.answer(
            "Слишком длинный текст (максимум 4000 символов). Введите короче:",
            reply_markup=akb.cancel_kb(),
        )
        return
    await queries.set_setting(session, key, new_value)
    await state.clear()
    await message.answer(
        f"{E['check']} Текст «{_label(key)}» обновлён.\n\nПредпросмотр:\n\n{new_value}",
        reply_markup=akb.text_show_kb(key),
    )
