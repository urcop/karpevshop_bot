from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Золото 🥇"),
            KeyboardButton(text="Пополнить баланс 💳"),
            KeyboardButton(text="Профиль 📝"),
        ],
        [
            KeyboardButton(text="Кейсы 📦"),
            KeyboardButton(text="Отзывы 👥"),
            KeyboardButton(text="Другие товары 📦"),
        ],
        [
            KeyboardButton(text="Тех. поддержка 👤"),
        ],
    ], row_width=3, resize_keyboard=True
)
