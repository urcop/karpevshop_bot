from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import CommandStart


async def start(message: types.Message):
    await message.answer('Привет')


def register_start(dp: Dispatcher):
    dp.register_message_handler(start, CommandStart, state=None)
