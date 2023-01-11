from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

gold_menu_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text='Пополнить 🥇'),
            KeyboardButton(text='Вывести 🥇')
        ],
        [
            KeyboardButton(text='Посчитать 🥇'),
            KeyboardButton(text='Очередь 👥')
        ],
        [
            KeyboardButton(text='Игры 🎲'),
            KeyboardButton(text='Награды 🎁')
        ],
        [
            KeyboardButton(text='Главное меню ⬅️')
        ]
    ]
)
