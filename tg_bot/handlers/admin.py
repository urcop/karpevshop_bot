from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Command

from tg_bot.models.users import User
from tg_bot.services.broadcast import broadcast


async def broadcaster(message: types.Message):
    session_maker = message.bot['db']
    text = message.text[4:]
    users = [i[0] for i in await User.get_all_users(session_maker=session_maker)]
    await broadcast(bot=message.bot, users=users, text=text, disable_notifications=True)


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(broadcaster, Command(['ads']), is_admin=True)
