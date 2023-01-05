from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

support_callback = CallbackData('support', 'question_id')
support_menu_callback = CallbackData('support_menu', 'action')

keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='1', callback_data=support_callback.new(1)),
            InlineKeyboardButton(text='2', callback_data=support_callback.new(2)),
            InlineKeyboardButton(text='3', callback_data=support_callback.new(3)),
        ],
        [
            InlineKeyboardButton(text='4', callback_data=support_callback.new(4)),
            InlineKeyboardButton(text='5', callback_data=support_callback.new(5)),
            InlineKeyboardButton(text='6', callback_data=support_callback.new(6)),
        ],
        [
            InlineKeyboardButton(text='7', callback_data=support_callback.new(7)),
            InlineKeyboardButton(text='Связаться', callback_data=support_menu_callback.new('contact')),

        ]
    ], row_width=3
)

answer_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Связаться', callback_data=support_menu_callback.new('contact'))
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=support_menu_callback.new('back'))
        ]
    ], row_width=1
)