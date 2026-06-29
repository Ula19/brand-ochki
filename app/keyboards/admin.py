from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Brand, Category, Product
from app.utils.formatting import format_price


def admin_main() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📂 Категории", callback_data="admin:c:list")
    b.button(text="🏷 Бренды", callback_data="admin:b:list")
    b.button(text="📦 Товары", callback_data="admin:p:section")
    b.button(text="📝 Тексты", callback_data="admin:t:menu")
    b.adjust(2, 2)
    return b.as_markup()


def texts_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📍 О магазине", callback_data="admin:t:show:shop_info")
    b.button(text="📞 Контакты", callback_data="admin:t:show:contacts")
    b.button(text="⬅️ В админ-панель", callback_data="admin:menu")
    b.adjust(1)
    return b.as_markup()


def text_show_kb(key: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Изменить", callback_data=f"admin:t:edit:{key}")
    b.button(text="⬅️ К списку текстов", callback_data="admin:t:menu")
    b.adjust(1)
    return b.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data="admin:cancel")
    return b.as_markup()


# ---------- Категории ----------

def categories_admin(categories: list[Category]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for cat in categories:
        prefix = "✅" if cat.is_active else "❌"
        b.button(text=f"{prefix} {cat.name}", callback_data=f"admin:c:toggle:{cat.id}")
    b.adjust(1)
    actions = InlineKeyboardBuilder()
    actions.button(text="➕ Добавить категорию", callback_data="admin:c:add")
    actions.button(text="⬅️ В админ-панель", callback_data="admin:menu")
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


# ---------- Бренды ----------

def brands_admin(brands: list[Brand]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for br in brands:
        prefix = "✅" if br.is_active else "❌"
        b.button(text=f"{prefix} {br.name}", callback_data=f"admin:b:toggle:{br.id}")
    b.adjust(1)
    actions = InlineKeyboardBuilder()
    actions.button(text="➕ Добавить бренд", callback_data="admin:b:add")
    actions.button(text="⬅️ В админ-панель", callback_data="admin:menu")
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


# ---------- Товары: раздел и список ----------

def products_section(categories: list[Category]) -> InlineKeyboardMarkup:
    """Раздел товаров: список категорий + кнопка добавить товар."""
    b = InlineKeyboardBuilder()
    b.button(text="➕ Добавить товар", callback_data="admin:p:add")
    b.adjust(1)
    cats = InlineKeyboardBuilder()
    for cat in categories:
        cats.button(text=cat.name, callback_data=f"admin:p:list:{cat.id}:0")
    cats.adjust(2)
    b.attach(cats)
    back = InlineKeyboardBuilder()
    back.button(text="⬅️ В админ-панель", callback_data="admin:menu")
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
        prefix = "✅" if p.is_active else "❌"
        title = f"{prefix} {p.name} — {format_price(p.price, p.currency)} (ост: {p.stock})"
        b.button(text=title, callback_data=f"admin:p:show:{p.id}")
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
    back.button(text="⬅️ К разделу товаров", callback_data="admin:p:section")
    b.attach(back)
    return b.as_markup()


def product_admin_card(product: Product) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Цена", callback_data=f"admin:p:price:{product.id}")
    b.button(text="📦 Остаток", callback_data=f"admin:p:stock:{product.id}")
    on_off = "Деактивировать" if product.is_active else "Активировать"
    b.button(text=f"🔄 {on_off}", callback_data=f"admin:p:toggle:{product.id}")
    b.button(text="⬅️ К списку", callback_data=f"admin:p:list:{product.category_id}:0")
    b.adjust(2, 1, 1)
    return b.as_markup()


# ---------- FSM выборы ----------

def choose_currency() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="UZS (сум)", callback_data="fsm:cur:UZS")
    b.button(text="USD ($)", callback_data="fsm:cur:USD")
    b.button(text="❌ Отмена", callback_data="admin:cancel")
    b.adjust(2, 1)
    return b.as_markup()


def choose_brand(brands: list[Brand]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for br in brands:
        b.button(text=br.name, callback_data=f"fsm:brand:{br.id}")
    b.adjust(2)
    actions = InlineKeyboardBuilder()
    actions.button(text="➕ Новый бренд", callback_data="fsm:brand:new")
    actions.button(text="❌ Отмена", callback_data="admin:cancel")
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


def choose_category(categories: list[Category]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for cat in categories:
        b.button(text=cat.name, callback_data=f"fsm:cat:{cat.id}")
    b.adjust(2)
    actions = InlineKeyboardBuilder()
    actions.button(text="➕ Новая категория", callback_data="fsm:cat:new")
    actions.button(text="❌ Отмена", callback_data="admin:cancel")
    actions.adjust(1)
    b.attach(actions)
    return b.as_markup()


def new_brand_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ К списку брендов", callback_data="fsm:brand:back")
    b.button(text="❌ Отмена", callback_data="admin:cancel")
    b.adjust(1)
    return b.as_markup()


def new_category_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ К списку категорий", callback_data="fsm:cat:back")
    b.button(text="❌ Отмена", callback_data="admin:cancel")
    b.adjust(1)
    return b.as_markup()


def confirm_save() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Сохранить", callback_data="fsm:save")
    b.button(text="❌ Отмена", callback_data="admin:cancel")
    b.adjust(2)
    return b.as_markup()
