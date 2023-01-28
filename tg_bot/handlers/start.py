from aiogram import types, Dispatcher
from aiogram.dispatcher.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from tg_bot.keyboards.reply import main_menu


async def start(message: types.Message):
    text = [
        'Спасибо что выбрали нас!',
        'Выберите в меню, что хотите сделать.'
    ]
    await message.answer('\n'.join(text), reply_markup=main_menu.keyboard)


async def back_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Главное меню', reply_markup=main_menu.keyboard)


async def reset_state(message: types.Message, state: FSMContext):
    await state.finish()


def register_start(dp: Dispatcher):
    dp.register_message_handler(start, Command(['start']))
    dp.register_message_handler(back_main_menu, state="*", text='⬅️Назад')
    dp.register_message_handler(reset_state, Command(['reset_state']), state="*")
