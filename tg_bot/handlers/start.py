from aiogram import types, Dispatcher
from aiogram.dispatcher.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from tg_bot.keyboards.reply import main_menu
from tg_bot.models.users import Referral


async def start(message: types.Message):
    params = message.text.split(' ')
    if int(params[1]) == message.from_user.id:
        return
    if len(params) == 2:
        session_maker = message.bot['db']
        await Referral.add_user(db_session=session_maker,
                                telegram_id=message.from_user.id, referrer=int(params[1]))
        await message.bot.send_message(int(params[1]), f'{message.from_user.id} зарегистрировался по вашей ссылке')
    text = [
        'Спасибо что выбрали нас!',
        'Выберите в меню, что хотите сделать.',
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
