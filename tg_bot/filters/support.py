import typing

from aiogram.dispatcher.filters import BoundFilter

from tg_bot.models.users import User


class SupportFilter(BoundFilter):
    key = 'is_support'

    def __init__(self, is_support: typing.Optional[bool] = None):
        self.is_support = is_support

    async def check(self, obj):
        session_maker = obj.bot['db']
        if self.is_support is None:
            return False
        support_list = [user[0] for user in await User.get_supports(session_maker=session_maker)]
        return (obj.from_user.id in support_list) == self.is_support
