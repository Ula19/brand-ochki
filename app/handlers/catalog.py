from html import escape

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import queries
from app.emojis import E
from app.filters.admin import user_is_admin
from app.handlers.screen import clear_screen, save_screen
from app.keyboards import user as kb
from app.utils.formatting import format_price, format_product_card

router = Router()

PER_PAGE = 5
# Сколько брендов перечислять в шапке ленты, прежде чем свернуть в «и ещё N».
BRANDS_IN_HEADER = 3


# ---------- Фильтр каталога в FSM ----------
#
# Выбранных брендов может быть много, а callback_data ограничена 64 байтами —
# поэтому фильтр (категория, бренды, страница) живёт в состоянии, а кнопки
# несут только действие.

async def _get_filter(state: FSMContext) -> tuple[int, list[int], int]:
    data = await state.get_data()
    return int(data.get("cat_id") or 0), list(data.get("brand_ids") or []), int(data.get("page") or 0)


# ---------- Экраны ----------

async def _show_categories(bot: Bot, chat_id: int, state: FSMContext, session: AsyncSession) -> None:
    await clear_screen(bot, chat_id, state)
    await state.update_data(cat_id=0, brand_ids=[], page=0)
    categories = await queries.list_active_categories_with_products(session)
    if not categories:
        m = await bot.send_message(chat_id, "В каталоге пока нет товаров.", reply_markup=kb.to_menu_kb())
        await save_screen(state, [m.message_id])
        return
    m = await bot.send_message(
        chat_id,
        f"{E['bag']} <b>Каталог</b>\n\nВыберите категорию:",
        reply_markup=kb.categories_kb(categories),
    )
    await save_screen(state, [m.message_id])


async def _show_brand_select(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    session: AsyncSession,
    cat_id: int,
    selected: set[int],
) -> bool:
    """Экран выбора брендов. Возвращает False, если выбирать не из чего."""
    category = await queries.get_category(session, cat_id)
    if category is None or not category.is_active:
        return False
    brands = await queries.list_brands_in_category(session, cat_id)
    if len(brands) < 2:
        return False

    await clear_screen(bot, chat_id, state)
    text = (
        f"{E['folder']} <b>{escape(category.name)}</b>\n\n"
        "Отметьте нужные бренды и нажмите «Показать товары».\n"
        "Или сразу «Все бренды», чтобы посмотреть всю категорию."
    )
    m = await bot.send_message(chat_id, text, reply_markup=kb.brand_select_kb(brands, selected))
    await save_screen(state, [m.message_id])
    return True


async def _brands_label(session: AsyncSession, brand_ids: list[int]) -> str:
    if not brand_ids:
        return "Все бренды"
    brands = await queries.list_brands_by_ids(session, brand_ids)
    if not brands:
        return "Все бренды"
    names = [escape(b.name) for b in brands]
    if len(names) > BRANDS_IN_HEADER:
        return ", ".join(names[:BRANDS_IN_HEADER]) + f" и ещё {len(names) - BRANDS_IN_HEADER}"
    return ", ".join(names)


async def _show_feed(bot: Bot, chat_id: int, state: FSMContext, session: AsyncSession) -> None:
    cat_id, brand_ids, page = await _get_filter(state)
    category = await queries.get_category(session, cat_id) if cat_id else None
    if category is None or not category.is_active:
        # Фильтр протух (перезапуск бота, категорию скрыли) — уводим к категориям.
        await _show_categories(bot, chat_id, state, session)
        return

    await clear_screen(bot, chat_id, state)

    brands_in_cat = await queries.list_brands_in_category(session, cat_id)
    show_filter = len(brands_in_cat) >= 2

    total = await queries.count_active_products(session, cat_id, brand_ids)
    if total == 0:
        m = await bot.send_message(
            chat_id,
            f"{E['folder']} <b>{escape(category.name)}</b>\n\n"
            f"По фильтру «{await _brands_label(session, brand_ids)}» товаров нет.",
            reply_markup=kb.empty_feed_kb(show_filter),
        )
        await save_screen(state, [m.message_id])
        return

    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    page = max(0, min(page, total_pages - 1))
    await state.update_data(page=page)

    products = await queries.list_active_products(
        session, cat_id, PER_PAGE, page * PER_PAGE, brand_ids
    )

    msg_ids: list[int] = []
    for p in products:
        caption = (
            f"<b>{escape(p.name)}</b>\n"
            f"{escape(p.brand.name)}\n"
            f"{format_price(p.price, p.currency)}"
        )
        m = await _send_product_preview(bot, chat_id, p.photo_file_id, caption, kb.single_product_kb(p.id))
        msg_ids.append(m.message_id)

    control_text = (
        f"{E['folder']} {escape(category.name)}\n"
        f"{E['tag']} {await _brands_label(session, brand_ids)}\n"
        f"Товаров: {total} · Страница {page + 1}/{total_pages}"
    )
    control = await bot.send_message(
        chat_id,
        control_text,
        reply_markup=kb.feed_controls_kb(page, total_pages, show_filter, bool(brand_ids)),
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
async def choose_category(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(cat_id=cat_id, brand_ids=[], page=0)
    chat_id = callback.message.chat.id
    # Если бренд в категории один, выбирать нечего — сразу лента.
    if not await _show_brand_select(bot, chat_id, state, session, cat_id, set()):
        await _show_feed(bot, chat_id, state, session)
    await callback.answer()


@router.callback_query(F.data == "cf")
async def open_brand_select(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    cat_id, brand_ids, _ = await _get_filter(state)
    chat_id = callback.message.chat.id
    if not await _show_brand_select(bot, chat_id, state, session, cat_id, set(brand_ids)):
        await _show_feed(bot, chat_id, state, session)
    await callback.answer()


@router.callback_query(F.data.startswith("bt:"))
async def toggle_brand(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    brand_id = int(callback.data.split(":")[1])
    cat_id, brand_ids, _ = await _get_filter(state)
    if not cat_id:
        # Состояние потеряно (перезапуск бота) — начинаем каталог заново.
        await _show_categories(bot, callback.message.chat.id, state, session)
        await callback.answer()
        return
    if brand_id in brand_ids:
        brand_ids.remove(brand_id)
    else:
        brand_ids.append(brand_id)
    await state.update_data(brand_ids=brand_ids)

    brands = await queries.list_brands_in_category(session, cat_id)
    await callback.message.edit_reply_markup(reply_markup=kb.brand_select_kb(brands, set(brand_ids)))
    await callback.answer()


@router.callback_query(F.data == "ball")
async def show_all_brands(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    await state.update_data(brand_ids=[], page=0)
    await _show_feed(bot, callback.message.chat.id, state, session)
    await callback.answer()


@router.callback_query(F.data == "bshow")
async def show_selected_brands(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    _, brand_ids, _ = await _get_filter(state)
    if not brand_ids:
        await callback.answer("Отметьте хотя бы один бренд или нажмите «Все бренды».", show_alert=True)
        return
    await state.update_data(page=0)
    await _show_feed(bot, callback.message.chat.id, state, session)
    await callback.answer()


@router.callback_query(F.data.startswith("pg:"))
async def turn_page(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    await state.update_data(page=int(callback.data.split(":")[1]))
    await _show_feed(bot, callback.message.chat.id, state, session)
    await callback.answer()


@router.callback_query(F.data == "back")
async def back_to_feed(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    await _show_feed(bot, callback.message.chat.id, state, session)
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    product_id = int(callback.data.split(":")[1])
    product = await queries.get_product(session, product_id)
    if product is None or not product.is_active or product.stock <= 0:
        await callback.answer("Товар недоступен", show_alert=True)
        return

    chat_id = callback.message.chat.id
    await clear_screen(bot, chat_id, state)
    text = format_product_card(product)
    markup = kb.product_card_kb(product, settings.admin_username)
    m = await _send_product_preview(bot, chat_id, product.photo_file_id, text, markup)
    await save_screen(state, [m.message_id])
    await callback.answer()


@router.callback_query(F.data == "close")
async def close_screen(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    chat_id = callback.message.chat.id
    await clear_screen(bot, chat_id, state)
    await state.clear()
    is_admin = await user_is_admin(session, callback.from_user.id)
    await bot.send_message(
        chat_id,
        f"{E['home']} Главное меню:",
        reply_markup=kb.main_menu(is_admin),
    )
    await callback.answer()
