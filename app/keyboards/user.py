from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.database.models import Brand, Category, Product
from app.emojis import E_ID
from app.utils.formatting import buy_deeplink, format_price


# Reply-клавиатура не поддерживает премиум-эмодзи и цвет — оставляем обычные.
BTN_CATALOG = "🛍 Каталог"
BTN_SHOP_INFO = "📍 О магазине"
BTN_CONTACTS = "📞 Контакты"
BTN_ADMIN = "🛠 Админ-панель"


def main_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_CATALOG)
    builder.button(text=BTN_SHOP_INFO)
    builder.button(text=BTN_CONTACTS)
    if is_admin:
        builder.button(text=BTN_ADMIN)
        builder.adjust(1, 2, 1)
    else:
        builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)


def categories_kb(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat.name, callback_data=f"cat:{cat.id}:0:0",
            style="primary", icon_custom_emoji_id=E_ID["folder"],
        )
    builder.adjust(2)
    return builder.as_markup()


def single_product_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подробнее", callback_data=f"prod:{product_id}",
        style="primary", icon_custom_emoji_id=E_ID["info"],
    )
    return builder.as_markup()


def feed_controls_kb(
    category_id: int,
    brand_id: int,
    page: int,
    total_pages: int,
    show_brand_filter: bool,
    brand_name: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    nav_buttons = []
    if page > 0:
        nav_buttons.append(("‹ Назад", f"cat:{category_id}:{brand_id}:{page - 1}"))
    nav_buttons.append((f"{page + 1}/{total_pages}", "noop"))
    if page < total_pages - 1:
        nav_buttons.append(("Вперёд ›", f"cat:{category_id}:{brand_id}:{page + 1}"))
    nav_row = InlineKeyboardBuilder()
    for text, data in nav_buttons:
        nav_row.button(text=text, callback_data=data)
    nav_row.adjust(len(nav_buttons))
    builder.attach(nav_row)

    filter_row = InlineKeyboardBuilder()
    if brand_id:
        filter_row.button(
            text=f"Бренд: {brand_name} — сбросить",
            callback_data=f"cat:{category_id}:0:0",
            style="danger", icon_custom_emoji_id=E_ID["cross"],
        )
        filter_row.adjust(1)
        builder.attach(filter_row)
    elif show_brand_filter:
        filter_row.button(
            text="Фильтр по бренду", callback_data=f"cf:{category_id}",
            style="primary", icon_custom_emoji_id=E_ID["search"],
        )
        filter_row.adjust(1)
        builder.attach(filter_row)

    back_row = InlineKeyboardBuilder()
    back_row.button(text="К категориям", callback_data="catalog", icon_custom_emoji_id=E_ID["back"])
    builder.attach(back_row)
    return builder.as_markup()


def brand_filter_kb(brands: list[Brand], category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for br in brands:
        builder.button(
            text=br.name, callback_data=f"cat:{category_id}:{br.id}:0",
            style="primary", icon_custom_emoji_id=E_ID["tag"],
        )
    builder.adjust(2)
    actions = InlineKeyboardBuilder()
    actions.button(
        text="Все бренды", callback_data=f"cat:{category_id}:0:0",
        style="primary", icon_custom_emoji_id=E_ID["list"],
    )
    actions.button(text="К категориям", callback_data="catalog", icon_custom_emoji_id=E_ID["back"])
    actions.adjust(1)
    builder.attach(actions)
    return builder.as_markup()


def product_card_kb(product: Product, admin_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Купить", url=buy_deeplink(product, admin_username),
        style="success", icon_custom_emoji_id=E_ID["buy"],
    )
    builder.button(
        text="К списку", callback_data=f"cat:{product.category_id}:0:0",
        icon_custom_emoji_id=E_ID["back"],
    )
    builder.button(text="В меню", callback_data="close", icon_custom_emoji_id=E_ID["home"])
    builder.adjust(1)
    return builder.as_markup()


def empty_category_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="К категориям", callback_data="catalog", icon_custom_emoji_id=E_ID["back"])
    return builder.as_markup()
