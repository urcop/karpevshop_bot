import random

from aiogram import types, Dispatcher

from tg_bot.keyboards.inline_cases import cases_keyboard, cases_callback, case_keyboard, case_action_callback
from tg_bot.models.case import CaseItems
from tg_bot.models.users import User


async def cases(message: types.Message):
    session_maker = message.bot['db']
    await message.answer(
        text='Выберите кейс из списка',
        reply_markup=await cases_keyboard(session_maker=session_maker)
    )


async def case(call: types.CallbackQuery):
    data = call.data.split(':')
    channel_id = call.bot['config'].misc.channel_id
    # реализовать бесплатный кейс
    session_maker = call.bot['db']
    id = data[1]
    name = data[2]
    price = data[3]
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


async def case_action(call: types.CallbackQuery):
    data = call.data.split(":")
    action = data[1]
    session_maker = call.bot['db']
    if action == 'cancel':
        await call.message.edit_text(
            text='Выберите кейс из списка',
            reply_markup=await cases_keyboard(session_maker=session_maker)
        )
    elif action == 'buy':
        # доделать покупку кейсов и реализовать шансы выпадение айтемов
        price = int(data[2])
        case_id = int(data[3])
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
                text=f'Поздравляем, вам выпало <strong>{dropped_item}</strong> стоимостью <strong>{item_price}G</strong>.\n'
                     f'На ваш счет зачислено {item_price} золота'
            )
        else:
            await call.message.edit_text('У вас недостаточно средств')


def register_cases(dp: Dispatcher):
    dp.register_message_handler(cases, text='Кейсы 📦')
    dp.register_callback_query_handler(case, cases_callback.filter())
    dp.register_callback_query_handler(case_action, case_action_callback.filter())
