import datetime
import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tg_bot.keyboards.inline.access_buy_gold import access_keyboard
from tg_bot.keyboards.reply import main_menu
from tg_bot.keyboards.reply.back_to_gold_menu import back_to_gold_keyboard
from tg_bot.keyboards.reply.gold_menu import gold_menu_keyboard
from tg_bot.misc.prefixes import get_prefix_type, prefixes, get_prefix_type_reverse
from tg_bot.models.history import GoldHistory
from tg_bot.models.seasons import Season, Season2User
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
                                            gold=data['count_gold'])
        logging.info(f'Пользователь - {call.from_user.id} пополнил баланс на {data["count_gold"]}G')

        now = datetime.datetime.now().timestamp()
        current_season_id = await Season.get_current_season(session_maker, now)
        times = await Season.get_season_time(session_maker, current_season_id)

        gold_in_season = await GoldHistory.get_gold_user_period(session_maker, start_time=int(times[0]),
                                                                end_time=int(times[1]), user_id=call.from_user.id)
        prefix_type = await get_prefix_type(gold_in_season)
        current_prefix = await prefixes(prefix_type)
        prefix_in_db = await Season2User.get_user_prefix(session_maker=session_maker, telegram_id=call.from_user.id,
                                                         season_id=current_season_id)

        if current_prefix[1] != prefix_in_db:
            await Season2User.update_prefix(session_maker=session_maker, telegram_id=call.from_user.id,
                                            season_id=current_season_id, prefix=current_prefix[1])
            await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                    currency_type='gold', value=current_prefix[0])
            await call.message.answer(
                f'🎉 Поздравляем, вы получили награду в виде {current_prefix[0]} золота за достижение нового префикса. '
                f'Продолжайте открывать новые префиксы.')

            current_prefix_reverse = await get_prefix_type_reverse(prefix_in_db)
            logging.info(prefix_type - current_prefix_reverse)
            if prefix_type - current_prefix_reverse > 1:
                for row in range(current_prefix_reverse, prefix_type):
                    reward = await prefixes(row)
                    logging.info(reward)
                    logging.info(
                        await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=call.from_user.id,
                                                            gold=reward[0]))
                    logging.info(await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                                         currency_type='gold', value=reward[0]))
        await call.message.delete()
        await call.message.answer('Успешная покупка!', reply_markup=gold_menu_keyboard)
        await state.finish()


async def rewards(message: types.Message):
    session_maker = message.bot['db']
    now = datetime.datetime.now().timestamp()
    text = []
    current_season_id = await Season.get_current_season(session_maker, now)
    times = await Season.get_season_time(session_maker, current_season_id)

    current_prefix = await Season2User.get_user_prefix(session_maker=session_maker,
                                                       telegram_id=message.from_user.id,
                                                       season_id=current_season_id)
    current_prefix_type = await get_prefix_type_reverse(current_prefix)
    prev_prefix = await Season2User.get_user_prefix(session_maker=session_maker,
                                                    telegram_id=message.from_user.id,
                                                    season_id=current_season_id - 1)
    if current_season_id > 1:
        text.append(f'📂 {current_season_id - 1} Сезон: {prev_prefix}')

    text.append(f'📂 {current_season_id} Сезон: {current_prefix}')
    try:
        next_reward = await prefixes(current_prefix_type + 1)
        text.append(f'🎁 Следующая награда - {next_reward[0]}G')
    except KeyError:
        text.append(
            f'🎁 Вы блистательно справились с этим трудным путём, но это лишь начало чего-то более масштабного. '
            'Продолжайте идти по этому пути, но не сдавайте.'
        )
    next_season = datetime.datetime.fromtimestamp(times[1]) - datetime.datetime.fromtimestamp(now)
    text.append(
        f'\n🕛 Следующий сезон через {next_season.days} дней {next_season.seconds // 3600} часов '
        f'{next_season.seconds % 3600 // 60} минут'
    )
    await message.answer('\n'.join(text))


def register_gold(dp: Dispatcher):
    dp.register_message_handler(gold_menu, text='Золото 🥇')
    dp.register_message_handler(back_button, text='Главное меню ⬅️')
    dp.register_message_handler(back_to_gold_menu, text='Назад⬅️', state='*')
    dp.register_message_handler(gold_calculate, text='Посчитать 🥇')
    dp.register_message_handler(gold_exchange, text='Пополнить 🥇')
    dp.register_message_handler(get_gold_count, state='calculate_gold')
    dp.register_message_handler(get_count_gold_exchange, state='get_count_gold_exchange')
    dp.register_callback_query_handler(access_buy, state='get_count_gold_exchange', text='access_buy_gold')
    dp.register_message_handler(rewards, text='Награды 🎁')
