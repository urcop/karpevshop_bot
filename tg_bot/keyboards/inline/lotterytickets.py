from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

lottery_ticket_callback = CallbackData('lottery', 'id', 'name', 'price')
action_ticket_callback = CallbackData('lottery_ticket', 'id', 'action', 'price')


def generate_lottery_tickets_keyboard(tickets: list):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for ticket in tickets:
        data = str(ticket[0]).split(':')
        keyboard.add(InlineKeyboardButton(text=data[1],
                                          callback_data=lottery_ticket_callback.new(
                                              data[0],
                                              data[1],
                                              data[2]
                                          )))
    return keyboard


def buy_ticket_keyboard(ticket_id, price):
    keyboard = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f'Купить за {price}',
                                     callback_data=action_ticket_callback.new(ticket_id ,'buy', price))
            ],
            [
                InlineKeyboardButton(text='Назад',
                                     callback_data=action_ticket_callback.new(ticket_id, 'back', 0))
            ]
        ]
    )
    return keyboard
