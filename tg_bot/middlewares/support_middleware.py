from aiogram import types, Dispatcher
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from tg_bot.models.support import Tickets


class SupportMiddleware(BaseMiddleware):

    async def on_pre_process_message(self, message: types.Message, data: dict):
        dp: Dispatcher = message.bot['dp']
        state = dp.current_state(chat=message.from_user.id, user=message.from_user.id)

        state_str = str(await state.get_state())
        if message.text == '/stopdialog':
            session_maker = message.bot['db']
            await Tickets.update_status_by_user(support_id=message.from_user.id, status=-1, session_maker=session_maker)
            await message.answer('Вы завершили диалог с пользователем')
            data = await state.get_data()
            second_id = data.get("second_id")
            await message.bot.send_message(second_id, 'Диалог с агентом поддержки завершен')
            user_state = dp.current_state(chat=second_id, user=second_id)
            await user_state.finish()
            await state.finish()

            raise CancelHandler()
        if state_str == "in_support":
            data = await state.get_data()
            second_id = data.get("second_id")
            await message.copy_to(second_id)

            raise CancelHandler()
