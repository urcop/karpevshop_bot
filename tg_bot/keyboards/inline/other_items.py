import asyncio

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

other_items_callback = CallbackData('other_item', 'name', 'description', 'price', 'photo')
other_items_buy_callback = CallbackData('other_item_buy', 'name', 'price')
other_items_cancel_callback = CallbackData('other_item_cancel', 'action')


async def generate_other_items_keyboard(products):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for product in products:
        params = str(product[0]).split(':')
        name = params[0]
        description = params[1]
        price = params[2]
        photo = params[3]
        keyboard.insert(InlineKeyboardButton(text=products.index(product) + 1,
                                             callback_data=other_items_callback.new(name=name, description=description,
                                                                                    price=int(price), photo=photo)))
    return keyboard


async def buy_other_item_keyboard(name, price):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Купить', callback_data=other_items_buy_callback.new(name=name, price=price))
            ],
            [
                InlineKeyboardButton('Назад', callback_data=other_items_cancel_callback.new('cancel'))
            ]
        ]
    )
    return keyboard


if __name__ == '__main__':
    async def main():
        await generate_other_items_keyboard([('хуй:пизда:200:2.jpg',)])


    asyncio.run(main())
