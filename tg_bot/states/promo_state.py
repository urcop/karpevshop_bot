from aiogram.dispatcher.filters.state import State, StatesGroup


class PromoState(StatesGroup):
    code_name = State()
