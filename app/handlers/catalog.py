from html import escape

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import queries
from app.handlers.screen import clear_screen, save_screen
from app.keyboards import user as kb
from app.utils.formatting import format_price, format_product_card

router = Router()

PER_PAGE = 5


# ---------- Экраны ----------

async def _show_categories(bot: Bot, chat_id: int, state: FSMContext, session: AsyncSession) -> None:
    await clear_screen(bot, chat_id, state)
    categories = await queries.list_active_categories_with_products(session)
    if not categories:
        m = await bot.send_message(chat_id, "В каталоге пока нет товаров.")
        await save_screen(state, [m.message_id])
        return
    m = await bot.send_message(chat_id, "Выберите категорию:", reply_markup=kb.categories_kb(categories))
    await save_screen(state, [m.message_id])


async def _show_feed(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    session: AsyncSession,
    cat_id: int,
    brand_id: int,
    page: int,
) -> None:
    await clear_screen(bot, chat_id, state)

    category = await queries.get_category(session, cat_id)
    if category is None or not category.is_active:
        return

    total = await queries.count_active_products(session, cat_id, brand_id or None)
    if total == 0:
        m = await bot.send_message(
            chat_id,
            f"В категории «{category.name}» пока нет товаров.",
            reply_markup=kb.empty_category_back_kb(),
        )
        await save_screen(state, [m.message_id])
        return

    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    page = max(0, min(page, total_pages - 1))
    products = await queries.list_active_products(
        session, cat_id, PER_PAGE, page * PER_PAGE, brand_id or None
    )

    msg_ids: list[int] = []
    for p in products:
        caption = f"<b>{escape(p.name)}</b>\n{format_price(p.price, p.currency)}"
        markup = kb.single_product_kb(p.id)
        m = await _send_product_preview(bot, chat_id, p.photo_file_id, caption, markup)
        msg_ids.append(m.message_id)

    brands_in_cat = await queries.list_brands_in_category(session, cat_id)
    show_filter = len(brands_in_cat) >= 2
    brand_name = None
    if brand_id:
        brand = await queries.get_brand(session, brand_id)
        brand_name = brand.name if brand is not None else None

    header = f"📂 {category.name}"
    if brand_name:
        header += f" · {brand_name}"
    control_text = f"{header}\nТоваров: {total} · Страница {page + 1}/{total_pages}"
    control = await bot.send_message(
        chat_id,
        control_text,
        reply_markup=kb.feed_controls_kb(cat_id, brand_id, page, total_pages, show_filter, brand_name),
    )
    msg_ids.append(control.message_id)
    await save_screen(state, msg_ids)


async def _send_product_preview(bot: Bot, chat_id: int, photo_file_id: str, caption: str, markup):
    if photo_file_id:
        try:
            return await bot.send_photo(chat_id, photo_file_id, caption=caption, reply_markup=markup)
        except Exception:
            pass
    return await bot.send_message(chat_id, caption, reply_markup=markup)


# ---------- Хендлеры ----------

@router.message(F.text == kb.BTN_CATALOG)
async def open_catalog(message: Message, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    await clear_screen(bot, message.chat.id, state)
    await state.clear()
    await _show_categories(bot, message.chat.id, state, session)


@router.callback_query(F.data == "catalog")
async def back_to_categories(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    await _show_categories(bot, callback.message.chat.id, state, session)
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    # формат: cat:{cat_id}:{brand_id}:{page}, brand_id == 0 → все бренды
    _, cat_id_str, brand_id_str, page_str = callback.data.split(":")
    await _show_feed(
        bot,
        callback.message.chat.id,
        state,
        session,
        int(cat_id_str),
        int(brand_id_str),
        int(page_str),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cf:"))
async def choose_brand_filter(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    await clear_screen(bot, callback.message.chat.id, state)
    cat_id = int(callback.data.split(":")[1])
    category = await queries.get_category(session, cat_id)
    if category is None or not category.is_active:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    brands = await queries.list_brands_in_category(session, cat_id)
    m = await callback.message.answer(
        f"📂 {category.name}\n\nВыберите бренд:",
        reply_markup=kb.brand_filter_kb(brands, cat_id),
    )
    await save_screen(state, [m.message_id])
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    product_id = int(callback.data.split(":")[1])
    product = await queries.get_product(session, product_id)
    if product is None or not product.is_active or product.stock <= 0:
        await callback.answer("Товар недоступен", show_alert=True)
        return

    await clear_screen(bot, callback.message.chat.id, state)
    text = format_product_card(product)
    markup = kb.product_card_kb(product, settings.admin_username)
    m = await _send_product_preview(bot, callback.message.chat.id, product.photo_file_id, text, markup)
    await save_screen(state, [m.message_id])
    await callback.answer()


@router.callback_query(F.data == "close")
async def close_screen(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await clear_screen(bot, callback.message.chat.id, state)
    await callback.answer()
