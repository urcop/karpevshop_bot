from aiogram import types, Dispatcher
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils import exceptions

from tg_bot.keyboards.reply import main_menu
from tg_bot.models.support import Tickets


class SupportMiddleware(BaseMiddleware):

    async def on_pre_process_message(self, message: types.Message, data: dict):
        dp: Dispatcher = message.bot['dp']
        state = dp.current_state(chat=message.from_user.id, user=message.from_user.id)
        session_maker = message.bot['db']

        state_str = str(await state.get_state())
        if message.text == '/stopdialog':
            data = await state.get_data()
            second_id = data.get("second_id")
            if not second_id:
                return
            ticket_id = await Tickets.get_ticket_id_by_user_id(first_id=message.from_user.id, second_id=second_id,
                                                               session_maker=session_maker)
            support_id = await Tickets.get_support_id(ticket_id, session_maker)

            await Tickets.update_status(ticket_id=ticket_id, status=-1, session_maker=session_maker)
            queue = await Tickets.get_queue_tickets(session_maker)
            if message.from_user.id == support_id:
                await message.answer('Вы завершили диалог с пользователем')
                await message.answer(f'В очереди еще {queue} тикетов')
                try:
                    await message.bot.send_message(second_id, 'Диалог с агентом поддержки завершен',
                                                   reply_markup=main_menu.keyboard)
                except exceptions.BotBlocked:
                    return
            else:
                await message.bot.send_message(second_id, 'Пользователь завершил диалог')
                await message.bot.send_message(second_id, f'В очереди еще {queue} тикетов')
                await message.answer('Диалог с агентом поддержки завершен', reply_markup=main_menu.keyboard)

            user_state = dp.current_state(chat=second_id, user=second_id)
            await user_state.finish()
            await state.finish()

            raise CancelHandler()

        if state_str == "in_support":
            data = await state.get_data()
            second_id = data.get("second_id")
            await message.copy_to(second_id)

            raise CancelHandler()
