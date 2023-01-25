from aiogram import types
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from tg_bot.models.seasons import Season, Season2User
from tg_bot.models.users import User


class DbMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    async def pre_process(self, obj, data, *args):
        session_maker = obj.bot.get('db')
        telegram_user: types.User = obj.from_user
        user = await User.get_user(session_maker=session_maker, telegram_id=telegram_user.id)
        if not user:
            user = await User.add_user(
                session_maker,
                telegram_id=telegram_user.id,
                fullname=telegram_user.full_name,
                username=telegram_user.username,
            )
        await User.update_username_fullname(session_maker=session_maker, telegram_id=telegram_user.id,
                                            username=telegram_user.username, fullname=telegram_user.full_name)
        current_season_id = await Season.get_last_season(session_maker=session_maker)
        if not await Season2User.is_exists(session_maker=session_maker, telegram_id=obj.from_user.id,
                                           season_id=current_season_id):
            await Season2User.add_user_to_season(session_maker=session_maker, season_id=current_season_id,
                                                 telegram_id=obj.from_user.id)
        data['user'] = user
