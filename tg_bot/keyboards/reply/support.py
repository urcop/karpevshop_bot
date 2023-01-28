from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

support_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('/take'),
            KeyboardButton('/stopdialog')
        ]
    ]
)