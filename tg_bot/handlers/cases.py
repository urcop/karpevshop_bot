from aiogram import types, Dispatcher

from tg_bot.keyboards.inline_cases import cases_keyboard, cases_callback, case_keyboard, case_action
from tg_bot.models.case import CaseItems


async def cases(message: types.Message):
    session_maker = message.bot['db']
    await message.answer(
        text='Выберите кейс из списка',
        reply_markup=await cases_keyboard(session_maker=session_maker)
    )


async def case(call: types.CallbackQuery):
    data = call.data.split(':')
    channel_id = call.bot['config'].misc.chanel_id
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
        reply_markup=await case_keyboard(price))


async def action(call: types.CallbackQuery):
    data = call.data.split(":")
    session_maker = call.bot['db']
    if data[1] == 'cancel':
        await call.message.edit_text(
            text='Выберите кейс из списка',
            reply_markup=await cases_keyboard(session_maker=session_maker)
        )
    else:
        ...
        # доделать покупку кейсов и реализовать шансы выпадение айтемов

def register_cases(dp: Dispatcher):
    dp.register_message_handler(cases, text='Кейсы 📦')
    dp.register_callback_query_handler(case, cases_callback.filter())
    dp.register_callback_query_handler(action, case_action.filter())
