from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from tg_bot.models.case import Case

cases_callback = CallbackData('case', 'id', 'name', 'price')
case_action_callback = CallbackData('case_action', 'action', 'price', 'case_id')


async def cases_keyboard(session_maker):
    keyboard = InlineKeyboardMarkup(row_width=1)

    cases = await Case.get_visible_cases(session_maker=session_maker)
    for case in cases:
        id = str(case[0]).split(':')[0]
        name = str(case[0]).split(':')[1]
        price = str(case[0]).split(':')[2]
        keyboard.add(
            InlineKeyboardButton(
                text=name,
                callback_data=cases_callback.new(id, name, price)
            )
        )
    return keyboard


async def case_keyboard(case_id, case_price):
    keyboard = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'Купить за {case_price} руб',
                    callback_data=case_action_callback.new('buy', case_price, case_id)
                )
            ],
            [
                InlineKeyboardButton(
                    text='Назад',
                    callback_data=case_action_callback.new('cancel', 0, case_id)
                )
            ]
        ]
    )
    return keyboard
