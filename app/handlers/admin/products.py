from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import queries
from app.database.models import Product
from app.emojis import E
from app.keyboards import admin as akb
from app.states.admin import AddProduct, EditProductPrice, EditProductStock
from app.utils.formatting import format_price, parse_price, parse_stock

router = Router()

PER_PAGE = 8


# ---------- Раздел товаров и список ----------

@router.callback_query(F.data == "admin:p:section")
async def open_section(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    cats = await queries.list_all_categories(session)
    await callback.message.edit_text(
        f"{E['box']} <b>Товары</b>\n\nВыберите категорию для просмотра или добавьте новый товар:",
        reply_markup=akb.products_section(cats),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:p:list:"))
async def list_products(callback: CallbackQuery, session: AsyncSession) -> None:
    _, _, _, cat_id_s, page_s = callback.data.split(":")
    cat_id = int(cat_id_s)
    page = int(page_s)

    category = await queries.get_category(session, cat_id)
    if category is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    total = await queries.count_all_products_by_category(session, cat_id)
    if total == 0:
        await callback.message.edit_text(
            f"{E['box']} Товаров в категории «{escape(category.name)}» пока нет.",
            reply_markup=akb.products_admin_list([], cat_id, 0, 1),
        )
        await callback.answer()
        return

    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    page = max(0, min(page, total_pages - 1))
    products = await queries.list_all_products_by_category(session, cat_id, PER_PAGE, page * PER_PAGE)

    text = (
        f"{E['box']} Товары категории «<b>{escape(category.name)}</b>»\n"
        f"Всего: {total}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=akb.products_admin_list(products, cat_id, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:p:show:"))
async def show_product(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    product = await queries.get_product(session, product_id)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return
    await callback.message.edit_text(
        _format_admin_card(product),
        reply_markup=akb.product_admin_card(product),
    )
    await callback.answer()


def _format_admin_card(product: Product) -> str:
    status = f"{E['check']} активен" if product.is_active else f"{E['cross']} скрыт"
    return (
        f"{E['box']} <b>{escape(product.name)}</b>\n"
        f"Бренд: {escape(product.brand.name)}\n"
        f"Категория: {escape(product.category.name)}\n"
        f"Цена: {format_price(product.price, product.currency)}\n"
        f"Остаток: {product.stock}\n"
        f"Статус: {status}\n\n"
        f"{escape(product.description) or '<i>(без описания)</i>'}"
    )


# ---------- Переключение активности ----------

@router.callback_query(F.data.startswith("admin:p:toggle:"))
async def toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    new_state = await queries.toggle_product(session, product_id)
    if new_state is None:
        await callback.answer("Товар не найден", show_alert=True)
        return
    product = await queries.get_product(session, product_id)
    await callback.message.edit_text(
        _format_admin_card(product),
        reply_markup=akb.product_admin_card(product),
    )
    await callback.answer("Активирован." if new_state else "Скрыт.")


# ---------- Редактирование цены ----------

@router.callback_query(F.data.startswith("admin:p:price:"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    product = await queries.get_product(session, product_id)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return
    await state.set_state(EditProductPrice.waiting_value)
    await state.update_data(product_id=product_id, currency=product.currency)
    hint = "число в сумах (например: 450000)" if product.currency == "UZS" else "число в долларах (например: 12.50)"
    await callback.message.edit_text(
        f"Введите новую цену для «{escape(product.name)}».\nФормат: {hint}.",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(EditProductPrice.waiting_value, F.text)
async def edit_price_value(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    price = parse_price(message.text, data["currency"])
    if price is None:
        await message.answer("Не удалось разобрать цену. Введите ещё раз:", reply_markup=akb.cancel_kb())
        return
    await queries.update_product_price(session, data["product_id"], price)
    await state.clear()
    product = await queries.get_product(session, data["product_id"])
    await message.answer(
        f"{E['check']} Цена обновлена.\n\n{_format_admin_card(product)}",
        reply_markup=akb.product_admin_card(product),
    )


# ---------- Редактирование остатка ----------

@router.callback_query(F.data.startswith("admin:p:stock:"))
async def edit_stock_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    product = await queries.get_product(session, product_id)
    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return
    await state.set_state(EditProductStock.waiting_value)
    await state.update_data(product_id=product_id)
    await callback.message.edit_text(
        f"Введите новое количество для «{escape(product.name)}» (0 — нет в наличии):",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(EditProductStock.waiting_value, F.text)
async def edit_stock_value(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    stock = parse_stock(message.text)
    if stock is None:
        await message.answer(
            "Нужно неотрицательное целое число. Введите ещё раз:",
            reply_markup=akb.cancel_kb(),
        )
        return
    await queries.update_product_stock(session, data["product_id"], stock)
    await state.clear()
    product = await queries.get_product(session, data["product_id"])
    await message.answer(
        f"{E['check']} Остаток обновлён.\n\n{_format_admin_card(product)}",
        reply_markup=akb.product_admin_card(product),
    )


# ---------- Добавление товара (FSM) ----------

@router.callback_query(F.data == "admin:p:add")
async def add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddProduct.waiting_name)
    await state.update_data(data={})
    await callback.message.edit_text(
        "<b>Добавление товара</b> (шаг 1 из 8)\n\nВведите название товара:",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(AddProduct.waiting_name, F.text)
async def add_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name or len(name) > 200:
        await message.answer(
            "Название должно быть от 1 до 200 символов. Введите ещё раз:",
            reply_markup=akb.cancel_kb(),
        )
        return
    await state.update_data(name=name)
    await state.set_state(AddProduct.waiting_description)
    await message.answer(
        "<b>Шаг 2 из 8.</b> Введите описание товара. Сюда удобно положить размер, цвет, материал и прочее:",
        reply_markup=akb.cancel_kb(),
    )


@router.message(AddProduct.waiting_description, F.text)
async def add_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    await state.update_data(description=description)
    await state.set_state(AddProduct.waiting_currency)
    await message.answer(
        "<b>Шаг 3 из 8.</b> Выберите валюту:",
        reply_markup=akb.choose_currency(),
    )


@router.callback_query(AddProduct.waiting_currency, F.data.startswith("fsm:cur:"))
async def add_currency(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.rsplit(":", 1)[1]
    if currency not in ("UZS", "USD"):
        await callback.answer("Неизвестная валюта", show_alert=True)
        return
    await state.update_data(currency=currency)
    await state.set_state(AddProduct.waiting_price)
    hint = "число в сумах (например: 450000)" if currency == "UZS" else "число в долларах (например: 12.50)"
    await callback.message.edit_text(
        f"<b>Шаг 4 из 8.</b> Введите цену.\nФормат: {hint}.",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(AddProduct.waiting_price, F.text)
async def add_price(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    price = parse_price(message.text, data["currency"])
    if price is None or price == 0:
        await message.answer(
            "Не удалось разобрать цену (или она равна нулю). Введите ещё раз:",
            reply_markup=akb.cancel_kb(),
        )
        return
    await state.update_data(price=price)
    await state.set_state(AddProduct.waiting_stock)
    await message.answer(
        "<b>Шаг 5 из 8.</b> Введите количество товара на складе (целое число ≥ 0):",
        reply_markup=akb.cancel_kb(),
    )


@router.message(AddProduct.waiting_stock, F.text)
async def add_stock(message: Message, state: FSMContext, session: AsyncSession) -> None:
    stock = parse_stock(message.text)
    if stock is None:
        await message.answer(
            "Нужно неотрицательное целое число. Введите ещё раз:",
            reply_markup=akb.cancel_kb(),
        )
        return
    await state.update_data(stock=stock)
    await state.set_state(AddProduct.waiting_brand)
    brands = await queries.list_active_brands(session)
    await message.answer(
        "<b>Шаг 6 из 8.</b> Выберите бренд:",
        reply_markup=akb.choose_brand(brands),
    )


@router.callback_query(AddProduct.waiting_brand, F.data == "fsm:brand:new")
async def add_brand_new_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddProduct.waiting_new_brand_name)
    await callback.message.edit_text(
        "Введите название нового бренда (до 100 символов):",
        reply_markup=akb.new_brand_kb(),
    )
    await callback.answer()


@router.callback_query(AddProduct.waiting_new_brand_name, F.data == "fsm:brand:back")
async def add_brand_new_back(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.set_state(AddProduct.waiting_brand)
    brands = await queries.list_active_brands(session)
    await callback.message.edit_text(
        "<b>Шаг 6 из 8.</b> Выберите бренд:",
        reply_markup=akb.choose_brand(brands),
    )
    await callback.answer()


@router.message(AddProduct.waiting_new_brand_name, F.text)
async def add_brand_new_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()
    if not name or len(name) > 100:
        await message.answer(
            "Название должно быть от 1 до 100 символов. Введите ещё раз:",
            reply_markup=akb.new_brand_kb(),
        )
        return
    try:
        brand = await queries.create_brand(session, name)
    except IntegrityError:
        await session.rollback()
        await message.answer(
            f"Бренд «{name}» уже существует. Введите другое название или вернитесь к списку:",
            reply_markup=akb.new_brand_kb(),
        )
        return
    await state.update_data(brand_id=brand.id, brand_name=brand.name)
    await state.set_state(AddProduct.waiting_category)
    categories = await queries.list_active_categories(session)
    await message.answer(
        f"{E['check']} Бренд «{escape(brand.name)}» создан.\n\n<b>Шаг 7 из 8.</b> Выберите категорию:",
        reply_markup=akb.choose_category(categories),
    )


@router.callback_query(AddProduct.waiting_brand, F.data.startswith("fsm:brand:"))
async def add_brand(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    brand_id = int(callback.data.rsplit(":", 1)[1])
    brand = await queries.get_brand(session, brand_id)
    if brand is None or not brand.is_active:
        await callback.answer("Бренд недоступен", show_alert=True)
        return
    await state.update_data(brand_id=brand_id, brand_name=brand.name)
    await state.set_state(AddProduct.waiting_category)
    categories = await queries.list_active_categories(session)
    await callback.message.edit_text(
        "<b>Шаг 7 из 8.</b> Выберите категорию:",
        reply_markup=akb.choose_category(categories),
    )
    await callback.answer()


@router.callback_query(AddProduct.waiting_category, F.data == "fsm:cat:new")
async def add_category_new_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddProduct.waiting_new_category_name)
    await callback.message.edit_text(
        "Введите название новой категории (до 100 символов):",
        reply_markup=akb.new_category_kb(),
    )
    await callback.answer()


@router.callback_query(AddProduct.waiting_new_category_name, F.data == "fsm:cat:back")
async def add_category_new_back(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.set_state(AddProduct.waiting_category)
    categories = await queries.list_active_categories(session)
    await callback.message.edit_text(
        "<b>Шаг 7 из 8.</b> Выберите категорию:",
        reply_markup=akb.choose_category(categories),
    )
    await callback.answer()


@router.message(AddProduct.waiting_new_category_name, F.text)
async def add_category_new_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()
    if not name or len(name) > 100:
        await message.answer(
            "Название должно быть от 1 до 100 символов. Введите ещё раз:",
            reply_markup=akb.new_category_kb(),
        )
        return
    try:
        category = await queries.create_category(session, name)
    except IntegrityError:
        await session.rollback()
        await message.answer(
            f"Категория «{name}» уже существует. Введите другое название или вернитесь к списку:",
            reply_markup=akb.new_category_kb(),
        )
        return
    await state.update_data(category_id=category.id, category_name=category.name)
    await state.set_state(AddProduct.waiting_photo)
    await message.answer(
        f"{E['check']} Категория «{escape(category.name)}» создана.\n\n"
        "<b>Шаг 8 из 8.</b> Пришлите фото товара (как фото, не как файл):",
        reply_markup=akb.cancel_kb(),
    )


@router.callback_query(AddProduct.waiting_category, F.data.startswith("fsm:cat:"))
async def add_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    cat_id = int(callback.data.rsplit(":", 1)[1])
    category = await queries.get_category(session, cat_id)
    if category is None or not category.is_active:
        await callback.answer("Категория недоступна", show_alert=True)
        return
    await state.update_data(category_id=cat_id, category_name=category.name)
    await state.set_state(AddProduct.waiting_photo)
    await callback.message.edit_text(
        "<b>Шаг 8 из 8.</b> Пришлите фото товара (как фото, не как файл):",
        reply_markup=akb.cancel_kb(),
    )
    await callback.answer()


@router.message(AddProduct.waiting_photo, F.photo)
async def add_photo(message: Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await state.set_state(AddProduct.confirm)
    data = await state.get_data()
    await message.answer_photo(
        photo=file_id,
        caption=_format_new_product_preview(data),
        reply_markup=akb.confirm_save(),
    )


@router.message(AddProduct.waiting_photo)
async def add_photo_wrong(message: Message) -> None:
    await message.answer(
        "Пришлите фото как изображение (не как файл и не текст). Или нажмите «Отмена».",
        reply_markup=akb.cancel_kb(),
    )


def _format_new_product_preview(data: dict) -> str:
    return (
        "Проверьте товар:\n\n"
        f"<b>{escape(data['name'])}</b>\n"
        f"Бренд: {escape(data['brand_name'])}\n"
        f"Категория: {escape(data['category_name'])}\n"
        f"Цена: {format_price(data['price'], data['currency'])}\n"
        f"Остаток: {data['stock']}\n\n"
        f"{escape(data['description']) or '<i>(без описания)</i>'}"
    )


@router.callback_query(AddProduct.confirm, F.data == "fsm:save")
async def add_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    product = await queries.create_product(
        session,
        name=data["name"],
        description=data["description"],
        price=data["price"],
        currency=data["currency"],
        stock=data["stock"],
        photo_file_id=data["photo_file_id"],
        brand_id=data["brand_id"],
        category_id=data["category_id"],
    )
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        f"{E['check']} Товар «{escape(product.name)}» добавлен.",
        reply_markup=akb.product_admin_card(await queries.get_product(session, product.id)),
    )
    await callback.answer()
