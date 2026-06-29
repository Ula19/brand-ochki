from aiogram import Router

from app.filters.admin import IsAdmin
from app.handlers.admin import admins, brands, categories, menu, products, texts

admin_router = Router()
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())
admin_router.include_router(menu.router)
admin_router.include_router(categories.router)
admin_router.include_router(brands.router)
admin_router.include_router(products.router)
admin_router.include_router(texts.router)
admin_router.include_router(admins.router)
