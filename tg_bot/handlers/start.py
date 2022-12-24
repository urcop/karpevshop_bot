
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Command

from tg_bot.keyboards import reply_main_menu


async def start(message: types.Message):

    text = [
        'Спасибо что выбрали нас!',
        'Выберите в меню, что хотите сделать.'
    ]
    await message.answer('\n'.join(text), reply_markup=reply_main_menu.keyboard)


def register_start(dp: Dispatcher):
    dp.register_message_handler(start, Command(['start']))
