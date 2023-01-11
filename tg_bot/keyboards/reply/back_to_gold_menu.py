from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

back_to_gold_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text='Назад⬅️')
        ]
    ]
)