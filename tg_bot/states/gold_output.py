from aiogram.dispatcher.filters.state import StatesGroup, State


class GoldOutput(StatesGroup):
    count = State()
    type = State()
    category = State()
    quality = State()
    item_name = State()
    photo = State()
