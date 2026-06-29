from aiogram.fsm.state import State, StatesGroup


class AddCategory(StatesGroup):
    waiting_name = State()


class AddBrand(StatesGroup):
    waiting_name = State()


class AddProduct(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_currency = State()
    waiting_price = State()
    waiting_stock = State()
    waiting_brand = State()
    waiting_new_brand_name = State()
    waiting_category = State()
    waiting_new_category_name = State()
    waiting_photo = State()
    confirm = State()


class EditProductPrice(StatesGroup):
    waiting_value = State()


class EditProductStock(StatesGroup):
    waiting_value = State()


class EditSetting(StatesGroup):
    waiting_value = State()


class AddAdmin(StatesGroup):
    waiting_id = State()
