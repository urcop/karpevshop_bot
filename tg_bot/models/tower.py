import datetime

from sqlalchemy import String, Column, Integer, insert, select, func, BigInteger
from sqlalchemy.orm import sessionmaker

from tg_bot.services.db_base import Base


class TowerGames(Base):
    __tablename__ = 'tower_games'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    bet = Column(Integer)
    win = Column(Integer)
    unix_date = Column(Integer, default=datetime.datetime.now().timestamp())
    date = Column(String, default=(datetime.datetime.now()).strftime('%d.%m.%Y'))

    @classmethod
    async def add_game(cls, user_id: int, bet: int, win: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(
                user_id=user_id,
                bet=bet,
                win=win
            )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_count_games_period(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.count(cls.id))
            else:
                sql = select(func.count(cls.id)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_sum_win_period(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.win))
            else:
                sql = select(func.sum(cls.win)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_sum_bets_period(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.bet))
            else:
                sql = select(func.sum(cls.bet)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()
