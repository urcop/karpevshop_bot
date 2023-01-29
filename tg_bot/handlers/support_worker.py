from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from tg_bot.handlers.admin import returns_output, output, finish, tell
from tg_bot.keyboards.inline.output_items import returns_output_callback
from tg_bot.keyboards.reply import main_menu
from tg_bot.keyboards.reply.support import support_keyboard
from tg_bot.keyboards.reply.worker import worker_keyboard
from tg_bot.models.workers import Worker, Support


async def job(message: types.Message, state: FSMContext):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    if text[1] == 'off':
        await Worker.set_active(user_id=message.from_user.id, active=False, session_maker=session_maker)
        await Support.set_active(user_id=message.from_user.id, active=False, session_maker=session_maker)
        await message.answer('Вы закончили работу', reply_markup=main_menu.keyboard)
        await state.finish()
    else:
        if await Worker.auth_worker(user_id=message.from_user.id, password=text[1], session_maker=session_maker):
            await Worker.set_active(user_id=message.from_user.id, active=True, session_maker=session_maker)
            await state.set_state('worker_in_job')
            await message.answer('Успешная авторизация', reply_markup=worker_keyboard)
            return
        elif not await Worker.auth_worker(user_id=message.from_user.id, password=text[1], session_maker=session_maker):
            await message.answer('Неверный пароль')
            return

        elif await Support.auth_support(user_id=message.from_user.id, password=text[1], session_maker=session_maker):
            await Support.set_active(user_id=message.from_user.id, active=True, session_maker=session_maker)
            await state.set_state('support_in_job')
            await message.answer('Успешная авторизация', reply_markup=support_keyboard)
            return
        elif not await Support.auth_support(user_id=message.from_user.id, password=text[1],
                                            session_maker=session_maker):
            await message.answer('Неверный пароль')
            return


def register_support_worker_commands(dp: Dispatcher):
    dp.register_message_handler(job, Command(['job']), state=['support_in_job', None], is_support=True)
    dp.register_message_handler(job, Command(['job']), state=['worker_in_job', None], is_worker=True)

    dp.register_message_handler(output, Command(['output']), state='worker_in_job', is_worker=True)
    dp.register_message_handler(finish, Command(['finish']), state='worker_in_job', is_worker=True)
    dp.register_callback_query_handler(returns_output, returns_output_callback.filter(), state='worker_in_job',
                                       is_worker=True)

    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_support=True)
    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_worker=True)
