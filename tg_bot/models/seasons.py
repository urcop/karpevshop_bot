import asyncio
import datetime

from sqlalchemy import Column, Integer, String, insert, select
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
            sql = insert(cls)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def check_available_season(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.end_season >= datetime.datetime.now().timestamp())


class Season2User(Base):
    __tablename__ = 'season2user'
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer)
    telegram_id = Column(Integer)
    current_prefix = Column(String)


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)

        print(await Season.create_new_season(session_maker=session))


    asyncio.run(main())
