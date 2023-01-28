import typing

from aiogram.dispatcher.filters import BoundFilter

from tg_bot.models.users import User


class WorkerFilter(BoundFilter):
    key = 'is_worker'

    def __init__(self, is_worker: typing.Optional[bool] = None):
        self.is_worker = is_worker

    async def check(self, obj):
        session_maker = obj.bot['db']
        if self.is_worker is None:
            return False
        workers_list = [user[0] for user in await User.get_workers(session_maker=session_maker)]
        return (obj.from_user.id in workers_list) == self.is_worker
