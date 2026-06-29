"""Посев тестовых данных для разработки.

Запуск: .venv/bin/python -m app.seed

Идемпотентен — если в БД уже есть категории, ничего не делает.
Фото — публичные URL-плейсхолдеры (Telegram скачает их при первой отправке).
В Этапе 4 реальные товары будут добавляться через админ-FSM с настоящими file_id.
"""
import asyncio

from sqlalchemy import select, func

from app.database.base import async_session_maker
from app.database.models import Brand, Category, Product


PLACEHOLDER = "https://placehold.co/800x600/png"


async def main() -> None:
    async with async_session_maker() as session:
        existing = await session.scalar(select(func.count(Category.id)))
        if existing:
            print("База уже заполнена, пропускаю посев.")
            return

        cat_glasses = Category(name="Очки")
        cat_caps = Category(name="Кепки")
        cat_watches = Category(name="Часы")
        session.add_all([cat_glasses, cat_caps, cat_watches])

        brand_rayban = Brand(name="Ray-Ban")
        brand_nike = Brand(name="Nike")
        brand_casio = Brand(name="Casio")
        session.add_all([brand_rayban, brand_nike, brand_casio])

        await session.flush()

        session.add_all([
            Product(
                name="Ray-Ban Aviator",
                description="Классические авиаторы. Золотая оправа, поляризационные линзы.",
                price=450_000,
                currency="UZS",
                stock=5,
                photo_file_id=f"{PLACEHOLDER}?text=Ray-Ban+Aviator",
                brand_id=brand_rayban.id,
                category_id=cat_glasses.id,
            ),
            Product(
                name="Ray-Ban Wayfarer",
                description="Знаменитая модель Wayfarer. Чёрная оправа.",
                price=12000,  # USD: 120.00
                currency="USD",
                stock=3,
                photo_file_id=f"{PLACEHOLDER}?text=Ray-Ban+Wayfarer",
                brand_id=brand_rayban.id,
                category_id=cat_glasses.id,
            ),
            Product(
                name="Nike Cap Heritage 86",
                description="Бейсболка с регулируемым ремешком. Цвет: чёрный.",
                price=180_000,
                currency="UZS",
                stock=10,
                photo_file_id=f"{PLACEHOLDER}?text=Nike+Cap",
                brand_id=brand_nike.id,
                category_id=cat_caps.id,
            ),
            Product(
                name="Casio G-Shock GA-2100",
                description="Ударопрочные часы. Чёрный корпус, минеральное стекло.",
                price=1_400_000,
                currency="UZS",
                stock=2,
                photo_file_id=f"{PLACEHOLDER}?text=G-Shock",
                brand_id=brand_casio.id,
                category_id=cat_watches.id,
            ),
            Product(
                name="Casio Vintage A158WA",
                description="Классические электронные часы с браслетом из нержавейки.",
                price=5500,  # USD: 55.00
                currency="USD",
                stock=0,  # нет в наличии — не должно показаться юзеру
                photo_file_id=f"{PLACEHOLDER}?text=Casio+A158",
                brand_id=brand_casio.id,
                category_id=cat_watches.id,
            ),
        ])

        await session.commit()
        print("OK: посеяно 3 категории, 3 бренда, 5 товаров (один с stock=0).")


if __name__ == "__main__":
    asyncio.run(main())
