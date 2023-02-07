import datetime
import random

from aiogram import types, Dispatcher

from tg_bot.keyboards.inline.cases import cases_keyboard, cases_callback, case_keyboard, case_action_callback
from tg_bot.keyboards.inline.channel_sub import generate_channel_sub_keyboard
from tg_bot.models.case import CaseItems, FreeCaseCooldown
from tg_bot.models.history import GoldHistory, CaseHistory
from tg_bot.models.users import User


async def _give_free_case(session_maker, user_id):
    date = datetime.datetime.now()
    await FreeCaseCooldown.add_cooldown(session_maker=session_maker, telegram_id=user_id)
    gold = random.randint(1, 3)
    await User.add_currency(
        session_maker=session_maker,
        telegram_id=user_id,
        currency_type='gold',
        value=gold
    )
    await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=user_id, gold=gold, date=date)
    return f'На ваш счет зачислено {gold}G'


async def cases(message: types.Message):
    session_maker = message.bot['db']
    await message.answer(
        text='Выберите кейс из списка',
        reply_markup=await cases_keyboard(session_maker=session_maker)
    )


async def case(call: types.CallbackQuery, callback_data: dict):
    user_id = call.from_user.id
    channel_id = call.bot['config'].misc.channel_id
    session_maker = call.bot['db']
    id = callback_data.get('id')
    name = callback_data.get('name')
    price = callback_data.get('price')
    date = datetime.datetime.now()

    if int(price) == 0:
        user_channel_status = await call.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if user_channel_status['status'] != 'left':
            if await FreeCaseCooldown.is_exists(session_maker=session_maker, telegram_id=user_id):
                if await FreeCaseCooldown.is_active(session_maker=session_maker, telegram_id=user_id):
                    text = await _give_free_case(session_maker, user_id)
                    await call.message.answer(text)
                else:
                    time = await FreeCaseCooldown.get_remaining_time(session_maker=session_maker, telegram_id=user_id)
                    await call.message.answer('Вы уже открыли бесплатный кейс.\n'
                                              f'Следующий кейс будет доступен через: {time}')
            else:
                await FreeCaseCooldown.add_user_cooldown(session_maker=session_maker, telegram_id=user_id, date=date)
                text = await _give_free_case(session_maker, user_id)
                await call.message.answer(text)
        else:
            await call.message.edit_text(
                'Чтобы получить бесплатный кейс вы должны быть подписаны на группу\n'
                'После того как подписались нажмите кнопку "Я подписался"',
                reply_markup=generate_channel_sub_keyboard(channel_id))
    else:
        text = [f'Содержимое кейса {name}:\n']

        for item in await CaseItems.get_items_case_id(
                case_id=int(id),
                session_maker=session_maker):
            item_split = str(item[0]).split(':')
            name = item_split[2]
            item_price = item_split[3]
            text.append(f'{name} - {item_price}G')

        await call.message.edit_text(
            text='\n'.join(text),
            reply_markup=await case_keyboard(case_id=id, case_price=price))


async def case_action(call: types.CallbackQuery, callback_data: dict):
    action = callback_data.get('action')
    session_maker = call.bot['db']
    date = datetime.datetime.now()
    if action == 'cancel':
        await call.message.edit_text(
            text='Выберите кейс из списка',
            reply_markup=await cases_keyboard(session_maker=session_maker)
        )
    elif action == 'buy':
        price = int(callback_data.get('price'))
        case_id = int(callback_data.get('case_id'))
        user_balance = await User.get_balance(
            session_maker=session_maker,
            telegram_id=call.from_user.id
        )
        if user_balance >= price:
            await User.take_currency(session_maker=session_maker,
                                     telegram_id=call.from_user.id,
                                     currency_type='balance',
                                     value=price)
            all_chances = await CaseItems.get_chances_items(case_id=case_id, session_maker=session_maker)
            all_names = await CaseItems.get_names_items(case_id=case_id, session_maker=session_maker)
            names = [str(name[0]) for name in all_names]
            chances = [float(chance[0]) / 100 for chance in all_chances]
            dropped_item = random.choices(names, weights=chances)[0]
            item_price = await CaseItems.get_price_item(item_name=dropped_item, session_maker=session_maker)
            await User.add_currency(session_maker=session_maker,
                                    telegram_id=call.from_user.id,
                                    currency_type='gold',
                                    value=item_price)
            await call.message.edit_text(
                text=f'Поздравляем, вам выпало <strong>{dropped_item}</strong> '
                     f'стоимостью <strong>{item_price}G</strong>.\n'
                     f'На ваш счет зачислено {item_price} золота'
            )
            await CaseHistory.add_case_open(session_maker=session_maker, telegram_id=call.from_user.id,
                                            money_spent=price, gold_won=item_price, date=date)
            await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=call.from_user.id,
                                                gold=item_price, date=date)
        else:
            await call.message.edit_text('У вас недостаточно средств')
    elif action == 'subscribe':
        user_id = call.from_user.id
        channel_id = call.bot['config'].misc.channel_id
        user_channel_status = await call.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if user_channel_status['status'] != 'left':
            if await FreeCaseCooldown.is_exists(session_maker=session_maker, telegram_id=user_id):
                if await FreeCaseCooldown.is_active(session_maker=session_maker, telegram_id=user_id):
                    text = await _give_free_case(session_maker, user_id)
                    await call.message.answer(text)
                else:
                    time = await FreeCaseCooldown.get_remaining_time(session_maker=session_maker, telegram_id=user_id)
                    await call.message.edit_text('Вы уже открыли бесплатный кейс.\n'
                                                 f'Следующий кейс будет доступен через: {time}')
            else:
                await FreeCaseCooldown.add_user_cooldown(session_maker=session_maker, telegram_id=user_id, date=date)
                text = await _give_free_case(session_maker, user_id)
                await call.message.answer(text)
        else:
            await call.message.answer('Вы не подписаны на группу')
            await call.answer(cache_time=5)


def register_cases(dp: Dispatcher):
    dp.register_message_handler(cases, text='Кейсы 📦')
    dp.register_callback_query_handler(case, cases_callback.filter())
    dp.register_callback_query_handler(case_action, case_action_callback.filter())
