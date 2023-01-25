import calendar
import datetime

from aiogram import Bot

from tg_bot.models.history import GoldHistory
from tg_bot.models.seasons import Season
from tg_bot.models.users import User


async def top_month(bot: Bot):
    session_maker = bot['db']
    today = datetime.datetime.now() - datetime.timedelta(days=1)
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
    await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=int(top_users[0][0]), gold=1000)


async def top_week(bot: Bot):
    session_maker = bot['db']
    today = datetime.datetime.today() - datetime.timedelta(days=1)
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
    await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=int(top_week_users[0][0]), gold=500)


async def start_new_season(bot: Bot):
    session_maker = bot['db']
    if Season.check_available_season(session_maker):
        return

    now = datetime.datetime.now().timestamp()
