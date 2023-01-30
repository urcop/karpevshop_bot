from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

jackpot_callback = CallbackData('jackpot', 'room_id', 'action')


async def jackpot_keyboard(room_id: int = -1):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Обновить', callback_data=jackpot_callback.new(room_id, 'refresh'))
            ],
            [
                InlineKeyboardButton('Сделать ставки', callback_data=jackpot_callback.new(room_id, 'bet'))
            ]
        ]
    )
    return keyboard
