import asyncio

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

other_items_callback = CallbackData('other_item', 'id')
other_items_buy_callback = CallbackData('other_item_buy', 'id')
other_items_cancel_callback = CallbackData('other_item_cancel', 'action')


async def generate_other_items_keyboard(products):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for product in products:
        params = str(product[0])
        id = params[0]
        keyboard.insert(InlineKeyboardButton(text=products.index(product) + 1,
                                             callback_data=other_items_callback.new(id=id)))
    return keyboard


async def buy_other_item_keyboard(id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Купить', callback_data=other_items_buy_callback.new(id))
            ],
            [
                InlineKeyboardButton('Назад', callback_data=other_items_cancel_callback.new('cancel'))
            ]
        ]
    )
    return keyboard
