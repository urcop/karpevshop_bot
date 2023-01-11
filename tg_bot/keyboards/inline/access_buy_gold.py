from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

access_keyboard = InlineKeyboardMarkup(
    row_width=1,
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Подтвердить', callback_data='access_buy_gold')
        ]
    ]
)