from aiogram.dispatcher.filters.state import StatesGroup, State


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    photo = State()
