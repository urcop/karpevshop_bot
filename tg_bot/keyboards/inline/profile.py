from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='РЕФЕРАЛЬНАЯ СИСТЕМА', callback_data='profile_referral_system'),
            InlineKeyboardButton(text='ПРОМОКОД', callback_data='profile_promocode'),
        ],
        [
            InlineKeyboardButton(text='ТОП НЕДЕЛИ', callback_data='profile_top_week'),
            InlineKeyboardButton(text='ТОП МЕСЯЦА', callback_data='profile_top_month'),
        ],
        [
            InlineKeyboardButton(text='ПРАВИЛА', callback_data='profile_rules'),
        ]
    ], row_width=2
)
