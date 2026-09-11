from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.database.models import Brand, Category, Product
from app.emojis import E_ID
from app.utils.formatting import buy_deeplink


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


def _nav_row(*, categories: bool = False) -> InlineKeyboardBuilder:
    """Нижний ряд навигации: опционально «К категориям» + всегда «В меню»."""
    row = InlineKeyboardBuilder()
    if categories:
        row.button(text="К категориям", callback_data="catalog", icon_custom_emoji_id=E_ID["back"])
    row.button(text="В меню", callback_data="close", icon_custom_emoji_id=E_ID["home"])
    row.adjust(2 if categories else 1)
    return row


def to_menu_kb() -> InlineKeyboardMarkup:
    """Одинокая кнопка возврата — для информационных экранов."""
    return _nav_row().as_markup()


def categories_kb(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat.name, callback_data=f"cat:{cat.id}",
            style="primary", icon_custom_emoji_id=E_ID["folder"],
        )
    builder.adjust(2)
    builder.attach(_nav_row())
    return builder.as_markup()


def brand_select_kb(brands: list[Brand], selected: set[int]) -> InlineKeyboardMarkup:
    """Мультивыбор брендов: нажатие переключает галочку, показ — отдельной кнопкой."""
    builder = InlineKeyboardBuilder()
    for br in brands:
        chosen = br.id in selected
        builder.button(
            text=br.name, callback_data=f"bt:{br.id}",
            style="success" if chosen else "primary",
            icon_custom_emoji_id=E_ID["check"] if chosen else E_ID["tag"],
        )
    builder.adjust(2)

    actions = InlineKeyboardBuilder()
    if selected:
        actions.button(
            text=f"Показать товары ({len(selected)})", callback_data="bshow",
            style="success", icon_custom_emoji_id=E_ID["bag"],
        )
    actions.button(
        text="Все бренды", callback_data="ball",
        style="primary", icon_custom_emoji_id=E_ID["list"],
    )
    actions.adjust(1)
    builder.attach(actions)
    builder.attach(_nav_row(categories=True))
    return builder.as_markup()


def single_product_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подробнее", callback_data=f"prod:{product_id}",
        style="primary", icon_custom_emoji_id=E_ID["info"],
    )
    return builder.as_markup()


def feed_controls_kb(
    page: int,
    total_pages: int,
    show_brand_filter: bool,
    has_selection: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    nav_buttons: list[tuple[str, str]] = []
    if page > 0:
        nav_buttons.append(("‹ Назад", f"pg:{page - 1}"))
    nav_buttons.append((f"{page + 1}/{total_pages}", "noop"))
    if page < total_pages - 1:
        nav_buttons.append(("Вперёд ›", f"pg:{page + 1}"))
    nav_row = InlineKeyboardBuilder()
    for text, data in nav_buttons:
        nav_row.button(text=text, callback_data=data)
    nav_row.adjust(len(nav_buttons))
    builder.attach(nav_row)

    if show_brand_filter:
        filter_row = InlineKeyboardBuilder()
        filter_row.button(
            text="Изменить бренды" if has_selection else "Выбрать бренды",
            callback_data="cf",
            style="primary", icon_custom_emoji_id=E_ID["search"],
        )
        filter_row.adjust(1)
        builder.attach(filter_row)

    builder.attach(_nav_row(categories=True))
    return builder.as_markup()


def product_card_kb(product: Product, admin_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Купить", url=buy_deeplink(product, admin_username),
        style="success", icon_custom_emoji_id=E_ID["buy"],
    )
    builder.button(text="К списку", callback_data="back", icon_custom_emoji_id=E_ID["back"])
    builder.adjust(1)
    builder.attach(_nav_row(categories=True))
    return builder.as_markup()


def empty_feed_kb(show_brand_filter: bool) -> InlineKeyboardMarkup:
    """Лента без результатов: дать шанс поменять фильтр, а не только уйти назад."""
    builder = InlineKeyboardBuilder()
    if show_brand_filter:
        builder.button(
            text="Изменить бренды", callback_data="cf",
            style="primary", icon_custom_emoji_id=E_ID["search"],
        )
        builder.adjust(1)
    builder.attach(_nav_row(categories=True))
    return builder.as_markup()
