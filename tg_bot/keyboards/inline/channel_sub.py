from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.keyboards.inline.cases import case_action_callback


def generate_channel_sub_keyboard(channel_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Подписаться', url=f'https://t.me/{channel_id[1:]}'),
                InlineKeyboardButton('Я подписался', callback_data=case_action_callback.new('cancel', 0, 0))
            ]
        ], row_width=1
    )
    return keyboard