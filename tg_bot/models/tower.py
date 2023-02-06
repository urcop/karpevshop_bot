import asyncio
import datetime

from sqlalchemy import String, Column, Integer, insert, select, func, BigInteger
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class TowerGames(Base):
    __tablename__ = 'tower_games'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    bet = Column(Integer)
    win = Column(Integer)
    unix_date = Column(Integer)
    date = Column(String)

    @classmethod
    async def get_last_tower_game(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def add_game(cls, user_id: int, bet: int, win: int, session_maker: sessionmaker, date: datetime):
        async with session_maker() as db_session:
            unix_date = int(date.timestamp())
            admin_date = date.strftime('%d.%m.%Y')
            id = await cls.get_last_tower_game(session_maker)
            sql = insert(cls).values(
                id=id + 1 if id else 1,
                user_id=user_id,
                bet=bet,
                win=win,
                unix_date=unix_date,
                date=admin_date
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


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)
        now = int(datetime.datetime.now().timestamp())

        print(await TowerGames.add_game(user_id=1231231, bet=123, win=1231, session_maker=session))


    asyncio.run(main())
