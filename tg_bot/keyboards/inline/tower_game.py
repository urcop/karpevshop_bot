from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

tower_game_callback = CallbackData('tower_game', 'current_bet', 'current_step')
tower_game_end_callback = CallbackData('tower_game_end', 'current_bet')


def tower_game_keyboard(current_step: int = 0, current_bet: int = 0):
    keyboard = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Лево',
                                     callback_data=tower_game_callback.new(current_bet, current_step)),
                InlineKeyboardButton(text='Право',
                                     callback_data=tower_game_callback.new(current_bet, current_step))
            ]
        ]
    )

    if current_step > 0:
        keyboard.add(InlineKeyboardButton(text='Забрать выигрыш',
                                          callback_data=tower_game_end_callback.new(current_bet)))

    return keyboard