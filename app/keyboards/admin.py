from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Admin, Brand, Category, Product
from app.emojis import E_ID
from app.utils.formatting import format_price


def admin_main(is_superadmin: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Категории", callback_data="admin:c:list", style="primary", icon_custom_emoji_id=E_ID["folder"])
    b.button(text="Бренды", callback_data="admin:b:list", style="primary", icon_custom_emoji_id=E_ID["tag"])
    b.button(text="Товары", callback_data="admin:p:section", style="primary", icon_custom_emoji_id=E_ID["box"])
    b.button(text="Тексты", callback_data="admin:t:menu", style="primary", icon_custom_emoji_id=E_ID["memo"])
    if is_superadmin:
        b.button(text="Админы", callback_data="admin:adm:list", style="danger", icon_custom_emoji_id=E_ID["users"])
        b.adjust(2, 2, 1)
    else:
        b.adjust(2, 2)
    return b.as_markup()


# ---------- Тексты ----------

def texts_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="О магазине", callback_data="admin:t:show:shop_info", style="primary", icon_custom_emoji_id=E_ID["pin"])
    b.button(text="Контакты", callback_data="admin:t:show:contacts", style="primary", icon_custom_emoji_id=E_ID["phone"])
    b.button(text="В админ-панель", callback_data="admin:menu", icon_custom_emoji_id=E_ID["back"])
    b.adjust(1)
    return b.as_markup()


def text_show_kb(key: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Изменить", callback_data=f"admin:t:edit:{key}", style="primary", icon_custom_emoji_id=E_ID["edit"])
    b.button(text="К списку текстов", callback_data="admin:t:menu", icon_custom_emoji_id=E_ID["back"])
    b.adjust(1)
    return b.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Отмена", callback_data="admin:cancel", style="danger", icon_custom_emoji_id=E_ID["cross"])
    return b.as_markup()


# ---------- Категории ----------

def categories_admin(categories: list[Category]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for cat in categories:
        icon = E_ID["check"] if cat.is_active else E_ID["cross"]
        style = "success" if cat.is_active else "danger"
        b.button(text=cat.name, callback_data=f"admin:c:toggle:{cat.id}", style=style, icon_custom_emoji_id=icon)
    b.adjust(1)
    actions = InlineKeyboardBuilder()
    actions.button(text="Добавить категорию", callback_data="admin:c:add", style="primary", icon_custom_emoji_id=E_ID["plus"])
    actions.button(text="В админ-панель", callback_data="admin:menu", icon_custom_emoji_id=E_ID["back"])
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


# ---------- Бренды ----------

def brands_admin(brands: list[Brand]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for br in brands:
        icon = E_ID["check"] if br.is_active else E_ID["cross"]
        style = "success" if br.is_active else "danger"
        b.button(text=br.name, callback_data=f"admin:b:toggle:{br.id}", style=style, icon_custom_emoji_id=icon)
    b.adjust(1)
    actions = InlineKeyboardBuilder()
    actions.button(text="Добавить бренд", callback_data="admin:b:add", style="primary", icon_custom_emoji_id=E_ID["plus"])
    actions.button(text="В админ-панель", callback_data="admin:menu", icon_custom_emoji_id=E_ID["back"])
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


# ---------- Товары: раздел и список ----------

def products_section(categories: list[Category]) -> InlineKeyboardMarkup:
    """Раздел товаров: список категорий + кнопка добавить товар."""
    b = InlineKeyboardBuilder()
    b.button(text="Добавить товар", callback_data="admin:p:add", style="success", icon_custom_emoji_id=E_ID["plus"])
    b.adjust(1)
    cats = InlineKeyboardBuilder()
    for cat in categories:
        cats.button(text=cat.name, callback_data=f"admin:p:list:{cat.id}:0", style="primary", icon_custom_emoji_id=E_ID["folder"])
    cats.adjust(2)
    b.attach(cats)
    back = InlineKeyboardBuilder()
    back.button(text="В админ-панель", callback_data="admin:menu", icon_custom_emoji_id=E_ID["back"])
    b.attach(back)
    return b.as_markup()


def products_admin_list(
    products: list[Product],
    category_id: int,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        icon = E_ID["check"] if p.is_active else E_ID["cross"]
        title = f"{p.name} — {format_price(p.price, p.currency)} (ост: {p.stock})"
        b.button(text=title, callback_data=f"admin:p:show:{p.id}", style="primary", icon_custom_emoji_id=icon)
    b.adjust(1)

    nav = InlineKeyboardBuilder()
    if page > 0:
        nav.button(text="‹ Назад", callback_data=f"admin:p:list:{category_id}:{page - 1}")
    nav.button(text=f"{page + 1}/{total_pages}", callback_data="noop")
    if page < total_pages - 1:
        nav.button(text="Вперёд ›", callback_data=f"admin:p:list:{category_id}:{page + 1}")
    nav.adjust(3)
    b.attach(nav)

    back = InlineKeyboardBuilder()
    back.button(text="К разделу товаров", callback_data="admin:p:section", icon_custom_emoji_id=E_ID["back"])
    b.attach(back)
    return b.as_markup()


def product_admin_card(product: Product) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Цена", callback_data=f"admin:p:price:{product.id}", style="primary", icon_custom_emoji_id=E_ID["edit"])
    b.button(text="Остаток", callback_data=f"admin:p:stock:{product.id}", style="primary", icon_custom_emoji_id=E_ID["box"])
    if product.is_active:
        b.button(text="Деактивировать", callback_data=f"admin:p:toggle:{product.id}", style="danger", icon_custom_emoji_id=E_ID["refresh"])
    else:
        b.button(text="Активировать", callback_data=f"admin:p:toggle:{product.id}", style="success", icon_custom_emoji_id=E_ID["refresh"])
    b.button(text="К списку", callback_data=f"admin:p:list:{product.category_id}:0", icon_custom_emoji_id=E_ID["back"])
    b.adjust(2, 1, 1)
    return b.as_markup()


# ---------- FSM выборы ----------

def choose_currency() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="UZS (сум)", callback_data="fsm:cur:UZS", style="primary")
    b.button(text="USD ($)", callback_data="fsm:cur:USD", style="primary")
    b.button(text="Отмена", callback_data="admin:cancel", style="danger", icon_custom_emoji_id=E_ID["cross"])
    b.adjust(2, 1)
    return b.as_markup()


def choose_brand(brands: list[Brand]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for br in brands:
        b.button(text=br.name, callback_data=f"fsm:brand:{br.id}", style="primary", icon_custom_emoji_id=E_ID["tag"])
    b.adjust(2)
    actions = InlineKeyboardBuilder()
    actions.button(text="Новый бренд", callback_data="fsm:brand:new", style="success", icon_custom_emoji_id=E_ID["plus"])
    actions.button(text="Отмена", callback_data="admin:cancel", style="danger", icon_custom_emoji_id=E_ID["cross"])
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


def choose_category(categories: list[Category]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for cat in categories:
        b.button(text=cat.name, callback_data=f"fsm:cat:{cat.id}", style="primary", icon_custom_emoji_id=E_ID["folder"])
    b.adjust(2)
    actions = InlineKeyboardBuilder()
    actions.button(text="Новая категория", callback_data="fsm:cat:new", style="success", icon_custom_emoji_id=E_ID["plus"])
    actions.button(text="Отмена", callback_data="admin:cancel", style="danger", icon_custom_emoji_id=E_ID["cross"])
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


def new_brand_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="К списку брендов", callback_data="fsm:brand:back", icon_custom_emoji_id=E_ID["back"])
    b.button(text="Отмена", callback_data="admin:cancel", style="danger", icon_custom_emoji_id=E_ID["cross"])
    b.adjust(1)
    return b.as_markup()


def new_category_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="К списку категорий", callback_data="fsm:cat:back", icon_custom_emoji_id=E_ID["back"])
    b.button(text="Отмена", callback_data="admin:cancel", style="danger", icon_custom_emoji_id=E_ID["cross"])
    b.adjust(1)
    return b.as_markup()


def confirm_save() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Сохранить", callback_data="fsm:save", style="success", icon_custom_emoji_id=E_ID["check"])
    b.button(text="Отмена", callback_data="admin:cancel", style="danger", icon_custom_emoji_id=E_ID["cross"])
    b.adjust(2)
    return b.as_markup()


# ---------- Админы (только супер-админ) ----------

def admins_admin(admins: list[Admin]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for a in admins:
        label = f"@{a.username}" if a.username else f"ID {a.telegram_id}"
        b.button(text=label, callback_data=f"admin:adm:del:{a.telegram_id}", style="danger", icon_custom_emoji_id=E_ID["trash"])
    b.adjust(1)
    actions = InlineKeyboardBuilder()
    actions.button(text="Добавить админа", callback_data="admin:adm:add", style="success", icon_custom_emoji_id=E_ID["plus"])
    actions.button(text="В админ-панель", callback_data="admin:menu", icon_custom_emoji_id=E_ID["back"])
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


def confirm_remove_admin(telegram_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Да, удалить", callback_data=f"admin:adm:rm:{telegram_id}", style="danger", icon_custom_emoji_id=E_ID["trash"])
    b.button(text="Отмена", callback_data="admin:adm:list", icon_custom_emoji_id=E_ID["back"])
    b.adjust(1)
    return b.as_markup()
