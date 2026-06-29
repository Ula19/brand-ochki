from html import escape
from urllib.parse import quote

from app.database.models import Product


def format_price(price: int, currency: str) -> str:
    if currency == "UZS":
        return f"{price:,} сум".replace(",", " ")
    if currency == "USD":
        return f"${price // 100}.{price % 100:02d}"
    return f"{price} {currency}"


def parse_price(text: str, currency: str) -> int | None:
    """Парсит ввод цены. UZS — целые сумы; USD — может быть '12.50', хранится в центах."""
    cleaned = text.strip().replace(" ", "").replace(",", ".")
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value < 0:
        return None
    if currency == "UZS":
        return int(value)
    if currency == "USD":
        return int(round(value * 100))
    return None


def parse_stock(text: str) -> int | None:
    try:
        value = int(text.strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def format_product_card(product: Product) -> str:
    return (
        f"<b>{escape(product.name)}</b>\n"
        f"Бренд: {escape(product.brand.name)}\n"
        f"Категория: {escape(product.category.name)}\n"
        f"Цена: {format_price(product.price, product.currency)}\n\n"
        f"{escape(product.description)}"
    )


def buy_deeplink(product: Product, admin_username: str) -> str:
    msg = f"Здравствуйте! Хочу купить «{product.name}»"
    return f"https://t.me/{admin_username}?text={quote(msg)}"
