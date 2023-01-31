from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

payment_choice_callback = CallbackData('payment_choice', 'choice')

choice_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Оплатить через QIWI',
                callback_data=payment_choice_callback.new('QIWI')
            )
        ],
        [
            InlineKeyboardButton(
                text='Пополнить другим способом',
                callback_data=payment_choice_callback.new('another')
            )
        ]
    ]
)


def generate_qiwi_keyboard(payment_url):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Перейти к оплате',
                    url=payment_url
                )
            ],
            [
                InlineKeyboardButton(
                    text='Проверить оплату',
                    callback_data='payment_qiwi_success'
                )
            ],
            [
                InlineKeyboardButton(
                    text='Отмена',
                    callback_data='payment_qiwi_cancel'
                )
            ]
        ]
    )
    return keyboard


check = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="ОТПРАВИТЬ ЧЕК", callback_data='payment_check')
        ]
    ]
)
