import asyncio

from sqlalchemy import Column, Integer, String, BigInteger, insert, select, and_
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class Logs(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    message = Column(String)
    time = Column(String)
    date = Column(String)

    @classmethod
    async def add_log(cls, telegram_id: int, message: str, time: str, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(telegram_id=telegram_id, message=message, time=time, date=date)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_user_logs(cls, telegram_id: int, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.time, cls.message).where(and_(cls.telegram_id == telegram_id, cls.date == date))
            result = await db_session.execute(sql)
            return result.all()


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)

        print(await Logs.get_user_logs(123134234, '10.02.2023', session))

    asyncio.run(main())
