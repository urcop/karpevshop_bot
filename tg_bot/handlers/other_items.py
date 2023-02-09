import logging

from aiogram import types, Dispatcher
from aiogram.types import InputFile

from tg_bot.keyboards.inline.other_items import generate_other_items_keyboard, other_items_callback, \
    buy_other_item_keyboard, other_items_buy_callback, other_items_cancel_callback
from tg_bot.models.product import Product
from tg_bot.models.users import User


async def other_items(message: types.Message):
    session_maker = message.bot['db']
    products = await Product.get_all_products(session_maker)
    text = ['Список доступных товаров:']
    if len(products) > 0:
        i = 0
        while i < len(products):
            name = str(products[i][0]).split(':')[0]
            text.append(f'{i + 1}: {name}')
            i += 1
        await message.answer('\n'.join(text), reply_markup=await generate_other_items_keyboard(products))
    else:
        await message.answer('На данный момент товары отсутствуют!')


async def other_item(call: types.CallbackQuery, callback_data: dict):
    config = call.bot['config']
    session_maker = call.bot['db']
    id = int(callback_data['id'])
    props = await Product.get_product_props(id=id, session_maker=session_maker)
    data = str(props[0]).split(':')
    name = data[0]
    description = data[1]
    price = int(data[2])
    photo = data[3]
    photo_path = config.misc.base_dir / 'uploads' / 'aprods' / photo
    photo = InputFile(photo_path)
    text = [
        f'<b>Название</b>: {name}',
        f'<b>Описание</b>: {description}',
        f'<b>Цена</b>: {price}',
    ]
    await call.message.delete()
    await call.message.answer_photo(photo=photo, caption='\n'.join(text),
                                    reply_markup=await buy_other_item_keyboard(id=id))


async def other_item_buy(call: types.CallbackQuery, callback_data: dict):
    session_maker = call.bot['db']
    id = int(callback_data['id'])
    props = await Product.get_product_props(id=id, session_maker=session_maker)
    data = str(props[0]).split(':')
    name = data[0]
    price = int(data[2])
    if await User.is_enough(telegram_id=call.from_user.id, currency_type='balance',
                            count=price, session_maker=session_maker):
        admins = [admin[0] for admin in await User.get_admins(session_maker)]
        await User.take_currency(session_maker, call.from_user.id,
                                 currency_type='balance', value=price)
        logging.info(f'Пользователь - {call.from_user.id} купил товар {name}')
        await Product.delete_product(id=id, session_maker=session_maker)
        await call.message.delete()
        await call.message.answer('Товар оплачен! Напишите @karpevg для его получения')
        for admin in admins:
            await call.bot.send_message(chat_id=admin,
                                        text='Куплен товар:\n'
                                             'Пользователь '
                                             f'{call.from_user.get_mention(str(call.from_user.id))}\n'
                                             f'Товар: {name}')

    else:
        await call.message.delete()
        await call.message.answer('У вас недостаточно средств')


async def other_item_cancel(call: types.CallbackQuery):
    session_maker = call.bot['db']
    products = await Product.get_all_products(session_maker)
    text = ['Список доступных товаров:']
    if len(products) > 0:
        i = 0
        while i < len(products):
            name = str(products[i][0]).split(':')[0]
            text.append(f'{i + 1}: {name}')
            i += 1
        await call.message.delete()
        await call.message.answer('\n'.join(text), reply_markup=await generate_other_items_keyboard(products))


def register_other_items(dp: Dispatcher):
    dp.register_message_handler(other_items, text='Другие товары 📦')
    dp.register_callback_query_handler(other_item, other_items_callback.filter())
    dp.register_callback_query_handler(other_item_buy, other_items_buy_callback.filter())
    dp.register_callback_query_handler(other_item_cancel, other_items_cancel_callback.filter())
