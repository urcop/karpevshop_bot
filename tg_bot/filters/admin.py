import typing

from aiogram.dispatcher.filters import BoundFilter

from tg_bot.models.users import User


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin: typing.Optional[bool] = None):
        self.is_admin = is_admin

    async def check(self, obj):
        session_maker = obj.bot['db']
        if self.is_admin is None:
            return False
        admin_list = [user[0] for user in await User.get_admins(session_maker=session_maker)]
        return (obj.from_user.id in admin_list) == self.is_admin
