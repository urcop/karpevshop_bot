from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

worker_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('/output'),
            KeyboardButton('/finish')
        ]
    ]
)