import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tg_bot.keyboards.inline.access_buy_gold import access_keyboard
from tg_bot.keyboards.reply import main_menu
from tg_bot.keyboards.reply.back_to_gold_menu import back_to_gold_keyboard
from tg_bot.keyboards.reply.gold_menu import gold_menu_keyboard
from tg_bot.models.history import GoldHistory
from tg_bot.models.users import User


async def gold_menu(message: types.Message):
    await message.answer('Выберите действие в меню', reply_markup=gold_menu_keyboard)


async def back_to_gold_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите действие в меню', reply_markup=gold_menu_keyboard)


async def back_button(message: types.Message):
    await message.answer('Главное меню ⬅️', reply_markup=main_menu.keyboard)


async def gold_calculate(message: types.Message, state: FSMContext):
    await state.set_state('calculate_gold')
    await message.answer('🥇 Введите количество золота', reply_markup=back_to_gold_keyboard)


async def gold_exchange(message: types.Message, state: FSMContext):
    await message.answer('🥇 Введите количество золота для пополнения', reply_markup=back_to_gold_keyboard)
    await state.set_state('get_count_gold_exchange')


async def get_gold_count(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        config = message.bot['config']
        try:
            data['count_gold'] = int(message.text)
        except ValueError:
            await message.answer('Введите целое число')
            return

        if data['count_gold'] >= config.misc.min_payment_value:
            price = int(data['count_gold'] * config.misc.gold_rate)
            await message.answer(f'Цена за {data["count_gold"]} золота, {price} руб.', reply_markup=gold_menu_keyboard)
            await state.finish()
        else:
            await message.answer(f'Можно купить минимум {config.misc.min_payment_value + 1} золота')
            return


async def get_count_gold_exchange(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        config = message.bot['config']
        session_maker = message.bot['db']
        try:
            data['count_gold'] = int(message.text)
        except ValueError:
            await message.answer('Введите целое число')
            return

        if data['count_gold'] >= config.misc.min_payment_value:
            price = int(data['count_gold'] * config.misc.gold_rate)
            if await User.is_enough(session_maker=session_maker, telegram_id=message.from_user.id,
                                    currency_type='balance', count=data['count_gold']):
                await message.answer(f'С вашего счета будет списано {price} руб. за {message.text} золота.',
                                     reply_markup=access_keyboard)

            else:
                await message.answer(f'Стоимость покупки {data["count_gold"]} золота составляет {price} руб.\n'
                                     'На вашем счете недостаточно средств. Пополните баланс.')
                return
            return
        else:
            await message.answer(f'Можно купить минимум {config.misc.min_payment_value + 1} золота')
            return


async def access_buy(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        session_maker = call.bot['db']
        config = call.bot['config']
        price = int(data['count_gold'] * config.misc.gold_rate)
        await User.take_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                 currency_type='balance', value=price)
        await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                currency_type='gold', value=data['count_gold'])
        await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=call.from_user.id,
                                            gold=price)
        logging.info(f'Пользователь - {call.from_user.id} пополнил баланс на {data["count_gold"]}G')
        await call.message.delete()
        await call.message.answer('Успешная покупка!', reply_markup=gold_menu_keyboard)
        await state.finish()


def register_gold(dp: Dispatcher):
    dp.register_message_handler(gold_menu, text='Золото 🥇')
    dp.register_message_handler(back_button, text='Главное меню ⬅️')
    dp.register_message_handler(back_to_gold_menu, text='Назад⬅️', state='*')
    dp.register_message_handler(gold_calculate, text='Посчитать 🥇')
    dp.register_message_handler(gold_exchange, text='Пополнить 🥇')
    dp.register_message_handler(get_gold_count, state='calculate_gold')
    dp.register_message_handler(get_count_gold_exchange, state='get_count_gold_exchange')
    dp.register_callback_query_handler(access_buy, state='get_count_gold_exchange', text='access_buy_gold')
