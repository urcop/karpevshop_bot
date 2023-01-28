import asyncio
import datetime

from sqlalchemy import Column, Integer, BigInteger, String, Boolean, insert, select, and_, update, delete, Float, func
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class Worker(Base):
    __tablename__ = 'workers'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    password = Column(String, default='1')
    active = Column(Boolean, default=False)

    @classmethod
    async def add_worker(cls, user_id: int, password: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(user_id=user_id, password=password)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def delete_worker(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = delete(cls).where(cls.user_id == user_id)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def auth_worker(cls, user_id: int, password: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(and_(user_id == cls.user_id, password == cls.password))
            result = await db_session.execute(sql)
            return True if result.first() else False

    @classmethod
    async def set_active(cls, user_id: int, active: bool, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(user_id == cls.user_id).values({'active': active})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result


class WorkerHistory(Base):
    __tablename__ = 'worker_history'
    id = Column(Integer, primary_key=True)
    worker_id = Column(BigInteger)
    gold = Column(Float)
    unix_date = Column(Integer, default=datetime.datetime.now().timestamp())
    date = Column(String, default=datetime.datetime.now().strftime('%d.%m.%Y'))

    @classmethod
    async def add_worker_history(cls, worker_id: int, gold: float, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(worker_id=worker_id, gold=gold)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_worker_stats(cls, session_maker: sessionmaker, worker_id: int, date: str):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.gold)).where(cls.worker_id == worker_id)
            else:
                sql = select(func.sum(cls.gold)).where(and_(cls.date == date, cls.worker_id == worker_id))
            result = await db_session.execute(sql)
            return result.scalar()


class Support(Base):
    __tablename__ = 'support'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    password = Column(String, default='1')
    active = Column(Boolean, default=False)
    active_ticket = Column(Integer, default=0)

    @classmethod
    async def add_support(cls, user_id: int, password: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(user_id=user_id, password=password)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def delete_support(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = delete(cls).where(cls.user_id == user_id)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def auth_support(cls, user_id: int, password: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(and_(user_id == cls.user_id, password == cls.password))
            result = await db_session.execute(sql)
            return True if result.first() else False

    @classmethod
    async def set_active(cls, user_id: int, active: bool, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(user_id == cls.user_id).values({'active': active})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)
        print(await Worker.delete_worker(5667987919, session_maker=session))


    asyncio.run(main())
