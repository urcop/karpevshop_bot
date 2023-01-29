import calendar
import datetime
import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tg_bot.keyboards.inline import profile
from tg_bot.keyboards.reply import main_menu, back_to_main
from tg_bot.misc.top_generators import generate_next_top_text, generate_text_top
from tg_bot.models.history import BalanceHistory, GoldHistory
from tg_bot.models.items import OutputQueue
from tg_bot.models.promocode import Promocode, User2Promo
from tg_bot.models.users import User
from tg_bot.states.promo_state import PromoState


async def get_profile(message: types.Message):
    # при нажатии на кнопку Профиль
    session_maker = message.bot['db']
    user = User(telegram_id=message.from_user.id)
    user_balance = await user.get_balance(session_maker, message.from_user.id)
    user_gold = await user.get_gold(session_maker, message.from_user.id)
    sum_purchases = await GoldHistory.get_sum_user_purchase(session_maker=session_maker,
                                                            telegram_id=message.from_user.id)
    count_outputs = await OutputQueue.get_user_requests(user_id=message.from_user.id, session_maker=session_maker)
    text = [
        f'🔑 ID: {message.from_user.id}',
        f'👤 Никнейм: {message.from_user.username if message.from_user.username else message.from_user.first_name}',
        f'💸 Баланс: {user_balance} руб.',
        f'💰 Золото: {user_gold}',
        f'⏰ Запросов на вывод золота: {count_outputs}',
        f'💵 Куплено золота: {sum_purchases} за все время'
    ]
    await message.answer('\n'.join(text), reply_markup=profile.keyboard)


# Профиль -> РЕФЕРАЛЬНАЯ СИСТЕМА
async def referral_system(call: types.CallbackQuery):
    session_maker = call.bot['db']
    user = User(telegram_id=call.from_user.id)
    count_refs = await user.count_referrals(session_maker, user)
    config = call.bot['config']
    text = [
        '❤️ За каждую покупку реферала вы получаете 5 золота',
        f'🔥 Ваша ссылка: https://t.me/{config.misc.bot_link}?start={call.from_user.id}',
        f'👥 Количество приглашенных пользователей: {count_refs if count_refs else 0}'
    ]

    await call.message.edit_text('\n'.join(text))


# Профиль -> ПРОМОКОД
async def promocode(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer('Введите промокод', reply_markup=back_to_main.keyboard)
    await PromoState.code_name.set()


async def promocode_code_name(message: types.Message, state: FSMContext):
    session_maker = message.bot['db']
    async with state.proxy() as data:
        data['code_name'] = message.text
        promo_name = data['code_name']
        is_valid = await Promocode.get_promo(code_name=promo_name, session_maker=session_maker)
        if is_valid:
            is_active = await Promocode.is_active(code_name=promo_name, session_maker=session_maker)
            if is_active:
                promo_type = await Promocode.get_promo_type(code_name=promo_name, session_maker=session_maker)
                promo_value = await Promocode.get_promo_value(code_name=promo_name, session_maker=session_maker)
                promo_id = await Promocode.get_id(code_name=promo_name, session_maker=session_maker)
                if not await User2Promo.get_user_promo(promo_id=promo_id, user_id=message.from_user.id,
                                                       session_maker=session_maker):
                    await User.add_currency(session_maker=session_maker, telegram_id=message.from_user.id,
                                            currency_type=promo_type, value=promo_value)
                    if promo_type == 'balance':
                        promo_type_text = 'рублей'
                        await BalanceHistory.add_balance_purchase(session_maker=session_maker,
                                                                  telegram_id=message.from_user.id,
                                                                  money=promo_value)
                    elif promo_type == 'gold':
                        promo_type_text = 'золота'
                        await GoldHistory.add_gold_purchase(session_maker=session_maker,
                                                            telegram_id=message.from_user.id,
                                                            gold=promo_value)

                    logging.info(f'Промокод {promo_name} - применен {message.from_user.id}')
                    await Promocode.decrement(promo_name, session_maker)
                    await User2Promo.add_user_promo(user_id=message.from_user.id, promo_id=promo_id,
                                                    session_maker=session_maker)
                    await state.finish()
                    await message.answer(f'Промокод успешно применен. Вы получили {promo_value} {promo_type_text}',
                                         reply_markup=main_menu.keyboard)
                else:
                    await message.answer('Вы уже активировали этот промокод')
            else:
                await message.answer('Промокод закончился')
        else:
            await message.answer('Промокод не существует, попробуйте заново')


# Профиль -> ТОП НЕДЕЛИ
async def top_week(call: types.CallbackQuery):
    session_maker = call.bot['db']
    today = datetime.datetime.today()
    today_weekday = datetime.datetime.weekday(today)
    monday = (today - datetime.timedelta(today_weekday)).replace(hour=0, minute=0, second=0)
    monday_unix = int(monday.timestamp())
    sunday = (monday + datetime.timedelta(6)).replace(hour=23, minute=59, second=59)
    sunday_unix = int(sunday.timestamp())

    top_week_users = await GoldHistory.get_history_period(session_maker=session_maker,
                                                          start_time=monday_unix,
                                                          end_time=sunday_unix)

    text: list = await generate_text_top(top_users=top_week_users, period='week')
    await call.message.edit_text('\n'.join(text))
    await call.message.answer(await generate_next_top_text(top_users=top_week_users, user_id=call.from_user.id))


# Профиль -> ТОП МЕСЯЦА
async def top_month(call: types.CallbackQuery):
    session_maker = call.bot['db']
    today = datetime.datetime.today()
    first_day_month_unix = int(datetime.datetime.replace(today, day=1, hour=0, minute=0, second=0).timestamp())
    last_day_month = (calendar.monthrange(today.year, today.month))[1]
    last_day_month_unix = int(datetime.datetime.replace(today, day=last_day_month, hour=23, minute=59,
                                                        second=59).timestamp())
    top_month_users = await GoldHistory.get_history_period(session_maker=session_maker,
                                                           start_time=first_day_month_unix,
                                                           end_time=last_day_month_unix)

    text: list = await generate_text_top(top_users=top_month_users, period='month')
    await call.message.edit_text('\n'.join(text))
    await call.message.answer(await generate_next_top_text(top_users=top_month_users, user_id=call.from_user.id))


# Профиль -> ПРАВИЛА
async def rules(call: types.CallbackQuery):
    await call.message.delete()
    text = [
        '1. Запрещено менять аватарку во время вывода.',
        '\t\t- Мы не несем ответственности за получение голды, если вы изменили аватарку.',
        '2. Запрещено снимать скин во время вывода.',
        '\t\t- Мы не несем ответственности за получение голды, если вы сняли скин и выставили опять.',
        '3. Запрещено менять цену скина.',
        '\t\t- Мы не несем ответственности за получение голды, если вы изменили цену скина во время вывода.',
        '4. Попытка обмана.',
        '\t\t- Блокировка аккаунта / обнуление',
        '5. Оскорбление.',
        '\t\t- Блокировка аккаунта / обнуление'
    ]
    await call.message.answer('\n'.join(text))


def register_profile(dp: Dispatcher):
    dp.register_message_handler(get_profile, text="Профиль 📝")
    dp.register_callback_query_handler(referral_system, text="profile_referral_system")
    dp.register_callback_query_handler(promocode, text="profile_promocode")
    dp.register_message_handler(promocode_code_name, state=PromoState.code_name)
    dp.register_callback_query_handler(top_week, text="profile_top_week")
    dp.register_callback_query_handler(top_month, text="profile_top_month")
    dp.register_callback_query_handler(rules, text="profile_rules")
