from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

choice_game_callback = CallbackData('choice_game', 'choice')
accept_game_callback = CallbackData('game', 'game_name')

games_keyboard = InlineKeyboardMarkup(
    row_width=1,
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Tower', callback_data=choice_game_callback.new('tower'))
        ],
        [
            InlineKeyboardButton(text='Jackpot', callback_data=choice_game_callback.new('jackpot'))
        ],
        [
            InlineKeyboardButton(text='Lottery', callback_data=choice_game_callback.new('lottery'))
        ]
    ]
)


def game_keyboard(game):
    keyboard = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Играть',
                                     callback_data=accept_game_callback.new(game))
            ]
        ]
    )
    return keyboard