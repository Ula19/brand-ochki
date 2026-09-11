from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Admin, Brand, Category, Product, Setting


# ---------- Категории ----------

async def list_active_categories_with_products(session: AsyncSession) -> list[Category]:
    """Активные категории, в которых есть хотя бы один доступный товар (для каталога юзера)."""
    stmt = (
        select(Category)
        .join(Product, Product.category_id == Category.id)
        .where(
            Category.is_active.is_(True),
            Product.is_active.is_(True),
            Product.stock > 0,
        )
        .distinct()
        .order_by(Category.name)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_active_categories(session: AsyncSession) -> list[Category]:
    """Все активные категории (для выбора при добавлении товара)."""
    stmt = select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_all_categories(session: AsyncSession) -> list[Category]:
    """Все категории, включая неактивные (для админки)."""
    stmt = select(Category).order_by(Category.is_active.desc(), Category.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    return await session.get(Category, category_id)


async def create_category(session: AsyncSession, name: str) -> Category:
    cat = Category(name=name)
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


async def toggle_category(session: AsyncSession, category_id: int) -> bool | None:
    """Переключает is_active и возвращает новое состояние или None если категория не найдена."""
    cat = await session.get(Category, category_id)
    if cat is None:
        return None
    cat.is_active = not cat.is_active
    await session.commit()
    return cat.is_active


# ---------- Бренды ----------

async def list_active_brands(session: AsyncSession) -> list[Brand]:
    stmt = select(Brand).where(Brand.is_active.is_(True)).order_by(Brand.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_all_brands(session: AsyncSession) -> list[Brand]:
    stmt = select(Brand).order_by(Brand.is_active.desc(), Brand.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_brand(session: AsyncSession, brand_id: int) -> Brand | None:
    return await session.get(Brand, brand_id)


async def create_brand(session: AsyncSession, name: str) -> Brand:
    brand = Brand(name=name)
    session.add(brand)
    await session.commit()
    await session.refresh(brand)
    return brand


async def toggle_brand(session: AsyncSession, brand_id: int) -> bool | None:
    brand = await session.get(Brand, brand_id)
    if brand is None:
        return None
    brand.is_active = not brand.is_active
    await session.commit()
    return brand.is_active


# ---------- Товары — публичный каталог ----------

def _active_product_conditions(category_id: int, brand_ids: list[int] | None):
    """Условия доступности товара. Пустой brand_ids — фильтра по бренду нет (все бренды)."""
    conditions = [
        Product.category_id == category_id,
        Product.is_active.is_(True),
        Product.stock > 0,
    ]
    if brand_ids:
        conditions.append(Product.brand_id.in_(brand_ids))
    return conditions


async def count_active_products(
    session: AsyncSession, category_id: int, brand_ids: list[int] | None = None
) -> int:
    stmt = select(func.count(Product.id)).where(*_active_product_conditions(category_id, brand_ids))
    result = await session.execute(stmt)
    return result.scalar_one()


async def list_active_products(
    session: AsyncSession,
    category_id: int,
    limit: int,
    offset: int,
    brand_ids: list[int] | None = None,
) -> list[Product]:
    stmt = (
        select(Product)
        .where(*_active_product_conditions(category_id, brand_ids))
        .order_by(Product.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_brands_in_category(session: AsyncSession, category_id: int) -> list[Brand]:
    """Активные бренды, у которых есть доступные товары в данной категории."""
    stmt = (
        select(Brand)
        .join(Product, Product.brand_id == Brand.id)
        .where(
            Product.category_id == category_id,
            Product.is_active.is_(True),
            Product.stock > 0,
            Brand.is_active.is_(True),
        )
        .distinct()
        .order_by(Brand.name)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_brands_by_ids(session: AsyncSession, brand_ids: list[int]) -> list[Brand]:
    """Бренды по списку ID — для подписи выбранного фильтра."""
    if not brand_ids:
        return []
    stmt = select(Brand).where(Brand.id.in_(brand_ids)).order_by(Brand.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    return await session.get(Product, product_id)


# ---------- Товары — админка ----------

async def count_all_products_by_category(session: AsyncSession, category_id: int) -> int:
    stmt = select(func.count(Product.id)).where(Product.category_id == category_id)
    result = await session.execute(stmt)
    return result.scalar_one()


async def list_all_products_by_category(
    session: AsyncSession, category_id: int, limit: int, offset: int
) -> list[Product]:
    """Все товары категории (включая stock=0 и неактивные) — для админки."""
    stmt = (
        select(Product)
        .where(Product.category_id == category_id)
        .order_by(Product.is_active.desc(), Product.stock.desc(), Product.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_product(
    session: AsyncSession,
    *,
    name: str,
    description: str,
    price: int,
    currency: str,
    stock: int,
    photo_file_id: str,
    brand_id: int,
    category_id: int,
) -> Product:
    product = Product(
        name=name,
        description=description,
        price=price,
        currency=currency,
        stock=stock,
        photo_file_id=photo_file_id,
        brand_id=brand_id,
        category_id=category_id,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def update_product_price(session: AsyncSession, product_id: int, price: int) -> bool:
    product = await session.get(Product, product_id)
    if product is None:
        return False
    product.price = price
    await session.commit()
    return True


async def update_product_stock(session: AsyncSession, product_id: int, stock: int) -> bool:
    product = await session.get(Product, product_id)
    if product is None:
        return False
    product.stock = stock
    await session.commit()
    return True


async def toggle_product(session: AsyncSession, product_id: int) -> bool | None:
    product = await session.get(Product, product_id)
    if product is None:
        return None
    product.is_active = not product.is_active
    await session.commit()
    return product.is_active


# ---------- Админы ----------

async def is_db_admin(session: AsyncSession, telegram_id: int) -> bool:
    """Есть ли пользователь среди добавленных супер-админом админов."""
    return await session.get(Admin, telegram_id) is not None


async def get_admin(session: AsyncSession, telegram_id: int) -> Admin | None:
    return await session.get(Admin, telegram_id)


async def list_admins(session: AsyncSession) -> list[Admin]:
    stmt = select(Admin).order_by(Admin.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def add_admin(
    session: AsyncSession, telegram_id: int, username: str, added_by: int
) -> Admin:
    admin = Admin(telegram_id=telegram_id, username=username, added_by=added_by)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def sync_admin_username(session: AsyncSession, telegram_id: int, username: str) -> None:
    """Обновляет @username админа, если он есть в БД и значение изменилось."""
    admin = await session.get(Admin, telegram_id)
    if admin is not None and admin.username != username:
        admin.username = username
        await session.commit()


async def remove_admin(session: AsyncSession, telegram_id: int) -> bool:
    admin = await session.get(Admin, telegram_id)
    if admin is None:
        return False
    await session.delete(admin)
    await session.commit()
    return True


# ---------- Настройки (key-value) ----------

async def get_setting(session: AsyncSession, key: str, *, default: str = "") -> str:
    obj = await session.get(Setting, key)
    return obj.value if obj is not None else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    obj = await session.get(Setting, key)
    if obj is None:
        session.add(Setting(key=key, value=value))
    else:
        obj.value = value
    await session.commit()
