from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('/output'),
            KeyboardButton('/finish'),
            KeyboardButton(text='⬅️Назад')
        ]
    ]
)
