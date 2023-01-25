import asyncio
import datetime

from sqlalchemy import Column, Integer, String, insert, select, func, BigInteger, and_, update
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class Season(Base):
    __tablename__ = 'season'
    id = Column(Integer, primary_key=True)
    start_season = Column(Integer, default=datetime.datetime.now().timestamp())
    end_season = Column(Integer, default=(datetime.datetime.now() + datetime.timedelta(90)).timestamp())

    @classmethod
    async def create_new_season(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            current_id = await cls.get_last_season(session_maker)
            try:
                sql = insert(cls).values(id=int(current_id) + 1)
            except:
                sql = insert(cls).values(id=1)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def check_available_season(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.end_season >= datetime.datetime.now().timestamp())
            result = await db_session.execute(sql)
            return True if result.first() else False

    @classmethod
    async def get_last_season(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_current_season(cls, session_maker: sessionmaker, time_now: [int, float]):
        async with session_maker() as db_session:
            sql = select(cls.id).where(cls.start_season <= time_now,
                                       cls.end_season >= time_now)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_season_time(cls, session_maker: sessionmaker, id: int):
        async with session_maker() as db_session:
            sql = select(cls.start_season, cls.end_season).where(cls.id == id)
            result = await db_session.execute(sql)
            return result.first()

    def __repr__(self):
        return f'{self.id}:{datetime.datetime.fromtimestamp(self.start_season).strftime("%d.%m.%Y")}'


class Season2User(Base):
    __tablename__ = 'season2user'
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer)
    telegram_id = Column(BigInteger)
    current_prefix = Column(String, default='Нет префикса')

    @classmethod
    async def add_user_to_season(cls, session_maker: sessionmaker, season_id: int, telegram_id: int):
        async with session_maker() as db_session:
            sql = insert(cls).values(season_id=season_id, telegram_id=telegram_id)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_user_season(cls, session_maker: sessionmaker, season_id: int):
        async with session_maker() as db_session:
            sql = select(cls.telegram_id).where(cls.season_id == season_id)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_user_prefix(cls, session_maker: sessionmaker, season_id: int, telegram_id: int):
        async with session_maker() as db_session:
            sql = select(cls.current_prefix).where(and_(cls.season_id == season_id, cls.telegram_id == telegram_id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def update_prefix(cls, session_maker: sessionmaker, telegram_id: int, season_id: int, prefix: str):
        async with session_maker() as db_session:
            sql = update(cls).where(and_(cls.season_id == season_id, cls.telegram_id == telegram_id)).values(
                {'current_prefix': prefix})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def is_exists(cls, session_maker: sessionmaker, telegram_id: int, season_id: int):
        async with session_maker() as db_session:
            sql = select(cls).where(and_(cls.season_id == season_id, cls.telegram_id == telegram_id))
            result = await db_session.execute(sql)
            return True if result.first() else False


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)
        now = int(datetime.datetime.now().timestamp())

        print(await Season.create_new_season(session_maker=session))
        # print(await Season.check_available_season(session_maker=session))


    asyncio.run(main())
