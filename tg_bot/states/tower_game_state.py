from aiogram.dispatcher.filters.state import StatesGroup, State


class TowerState(StatesGroup):
    current_bet = State()
