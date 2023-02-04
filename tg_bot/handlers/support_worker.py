from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from tg_bot.handlers.admin import returns_output, output, finish, tell
from tg_bot.keyboards.inline.output_items import returns_output_callback
from tg_bot.keyboards.inline.support import take_ticket_callback, report_ticket_callback, take_ticket_keyboard, \
    report_ticket_confirm
from tg_bot.keyboards.reply import main_menu
from tg_bot.keyboards.reply.support import support_keyboard, user_support_keyboard
from tg_bot.keyboards.reply.worker import worker_keyboard
from tg_bot.models.support import SupportBan, Tickets
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
        auth_worker = await Worker.auth_worker(user_id=message.from_user.id, password=text[1],
                                               session_maker=session_maker)
        support_auth = await Support.auth_support(user_id=message.from_user.id, password=text[1],
                                                  session_maker=session_maker)
        if auth_worker:
            await Worker.set_active(user_id=message.from_user.id, active=True, session_maker=session_maker)
            await state.set_state('worker_in_job')
            await message.answer('Успешная авторизация', reply_markup=worker_keyboard)
            return

        elif support_auth:
            await Support.set_active(user_id=message.from_user.id, active=True, session_maker=session_maker)
            await state.set_state('support_in_job')
            await message.answer('Успешная авторизация', reply_markup=support_keyboard)
            return

        elif not (support_auth and worker_keyboard):
            await message.answer('Неверный пароль')
            return


async def take(message: types.Message):
    session_maker = message.bot['db']
    ticket = await Tickets.get_available_ticket(session_maker=session_maker)
    if not ticket:
        await message.answer('Нет активных тикетов')
        return
    if await Tickets.support_in_dialog(support_id=message.from_user.id, session_maker=session_maker):
        await message.answer('Завершите предыдущий тикет')
        return
    ticket_info = str(ticket[0]).split(':')
    await Tickets.update_support_id(int(ticket_info[0]), support_id=message.from_user.id, session_maker=session_maker)
    text = [
        f'Тикет №{ticket_info[0]} от {ticket_info[3]}',
        f'ID Пользователя: {ticket_info[1]}\n',
        f'{ticket_info[2]}'
    ]
    await message.answer(text='\n'.join(text), reply_markup=await take_ticket_keyboard(ticket_info[0], ticket_info[1]))


async def take_action(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    session_maker = call.bot['db']
    action = callback_data.get('action')
    user_id = int(callback_data.get('user_id'))
    ticket_id = int(callback_data.get('ticket_id'))
    if action == 'cancel_dialog':
        await call.message.delete()
        await call.message.answer('Тикет отклонен')
        await call.bot.send_message(chat_id=user_id, text='Ваш тикет отклонен!')
        await Tickets.update_status(ticket_id=ticket_id, status=-2, session_maker=session_maker)
    if action == 'start_dialog':
        await call.message.delete_reply_markup()
        await call.message.answer('Вы начали диалог с пользователем')
        support_id = await Support.get_support_id(user_id=call.from_user.id, session_maker=session_maker)
        await call.bot.send_message(user_id, f'Агент тех поддержки №{support_id} начал диалог',
                                    reply_markup=user_support_keyboard)
        await Tickets.update_status(ticket_id=ticket_id, status=1, session_maker=session_maker)
        await state.set_state('in_support')
        dp: Dispatcher = call.bot['dp']
        user_state = dp.current_state(chat=user_id, user=user_id)
        await user_state.set_state('in_support')
        await user_state.update_data(second_id=call.from_user.id)
        await state.update_data(second_id=user_id)
    if action == 'warn_dialog':
        await call.message.edit_text('Вы хотите выдать предупреждение?',
                                     reply_markup=report_ticket_confirm(ticket_id, user_id))


async def report_ticket(call: types.CallbackQuery, callback_data: dict):
    session_maker = call.bot['db']
    action = callback_data.get('action')
    user_id = callback_data.get('user_id')
    ticket_id = callback_data.get('ticket_id')
    if action == 'yes':
        await SupportBan.add_ban(user_id=int(user_id), session_maker=session_maker)
        await Tickets.update_status(ticket_id=int(ticket_id), status=-2, session_maker=session_maker)
        await call.message.edit_text('Жалоба отправлена, тикет отклонен')
        await call.bot.send_message(int(user_id), 'Сотрудник поддержки выдал вам предупреждение!')
    if action == 'no':
        await call.message.edit_text('Жалоба отклонена, напишите /take еще раз')
        await Tickets.update_support_id(ticket_id=int(ticket_id), support_id=0, session_maker=session_maker)


def register_support_worker_commands(dp: Dispatcher):
    dp.register_message_handler(job, Command(['job']), state=['support_in_job', None], is_support=True)
    dp.register_message_handler(job, Command(['job']), state=['worker_in_job', None], is_worker=True)

    dp.register_message_handler(output, Command(['output']), state='worker_in_job', is_worker=True)
    dp.register_message_handler(finish, Command(['finish']), state='worker_in_job', is_worker=True)
    dp.register_callback_query_handler(returns_output, returns_output_callback.filter(), state='worker_in_job',
                                       is_worker=True)

    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_support=True)
    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_worker=True)

    dp.register_message_handler(take, Command(['take']), state=['support_in_job', None], is_support=True)

    dp.register_callback_query_handler(take_action, take_ticket_callback.filter(), state=['support_in_job', None],
                                       is_support=True)
    dp.register_callback_query_handler(report_ticket, report_ticket_callback.filter(), state=['support_in_job', None],
                                       is_support=True)
