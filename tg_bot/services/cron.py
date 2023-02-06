import calendar
import datetime

from aiogram import Bot

from tg_bot.models.history import GoldHistory
from tg_bot.models.seasons import Season, Season2User
from tg_bot.models.users import User


async def top_month(bot: Bot):
    session_maker = bot['db']
    date = datetime.datetime.now()
    today = date - datetime.timedelta(days=1)
    last_day_month = (calendar.monthrange(today.year, today.month))[1]
    last_day_month_unix = int(datetime.datetime.replace(today, day=last_day_month, hour=23, minute=59,
                                                        second=59).timestamp())
    first_day_unix = datetime.datetime.replace(today, day=1, hour=0, minute=0, second=0).timestamp()

    top_users = await GoldHistory.get_history_period(session_maker=session_maker, start_time=int(first_day_unix),
                                                     end_time=int(last_day_month_unix))

    await bot.send_message(chat_id=int(top_users[0][0]),
                           text='🎉 Поздравляем, вы получили 1000 золота за первое место в месяце')
    await User.add_currency(session_maker=session_maker, telegram_id=int(top_users[0][0]), currency_type='gold',
                            value=1000)
    await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=int(top_users[0][0]), gold=1000,
                                        date=date)


async def top_week(bot: Bot):
    session_maker = bot['db']
    date = datetime.datetime.now()
    today = date - datetime.timedelta(days=1)
    today_weekday = datetime.datetime.weekday(today)
    monday = (today - datetime.timedelta(today_weekday)).replace(hour=0, minute=0, second=0)
    monday_unix = int(monday.timestamp())
    sunday = (monday + datetime.timedelta(6)).replace(hour=23, minute=59, second=59)
    sunday_unix = int(sunday.timestamp())

    top_week_users = await GoldHistory.get_history_period(session_maker=session_maker,
                                                          start_time=monday_unix,
                                                          end_time=sunday_unix)
    await bot.send_message(chat_id=int(top_week_users[0][0]),
                           text='🎉 Поздравляем, вы получили 500 золота за первое место в неделе')
    await User.add_currency(session_maker=session_maker, telegram_id=int(top_week_users[0][0]), currency_type='gold',
                            value=500)
    date = datetime.datetime.now()
    await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=int(top_week_users[0][0]),
                                        gold=500, date=date)


async def start_new_season(bot: Bot):
    session_maker = bot['db']
    date = datetime.datetime.now()
    if await Season.check_available_season(session_maker):
        return
    prev_season_id = await Season.get_last_season(session_maker=session_maker)
    times = await Season.get_season_time(session_maker=session_maker, id=prev_season_id)
    top_user = await GoldHistory.get_history_period(session_maker=session_maker, start_time=times[0], end_time=times[1])
    await Season2User.update_prefix(session_maker=session_maker, season_id=prev_season_id,
                                    prefix='Всемогущественный', telegram_id=top_user[0][0])
    await User.add_currency(session_maker=session_maker, telegram_id=top_user[0][0],
                            currency_type='gold', value=3000)

    await bot.send_message(chat_id=int(top_user[0][0]),
                           text='🎉 Поздравляем, вы получили награду в виде 3000 золота за достижение префикса '
                                '<strong>Всемогущественный</strong>',
                           parse_mode='HTML')

    await Season.create_new_season(session_maker=session_maker, date=date)
    current_season_id = await Season.get_last_season(session_maker=session_maker)
    users = await Season2User.get_user_season(session_maker=session_maker, season_id=prev_season_id)
    for user_id in users:
        await Season2User.add_user_to_season(session_maker=session_maker, season_id=current_season_id,
                                             telegram_id=user_id[0])
