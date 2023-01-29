import asyncio
import datetime

from sqlalchemy import Column, Integer, String, insert, select, and_, BigInteger, update, delete, Float, func
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(Integer)
    category = Column(Integer)
    quality = Column(Integer)
    create_time = Column(Integer, default=datetime.datetime.now().timestamp())

    @classmethod
    async def add_item(cls, name: str, type: int,
                       category: int, quality: int,
                       session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(name=name, type=type, category=category, quality=quality)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def find_all_items(cls, type: int, category: int, quality: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.name).where(and_(cls.type == type, cls.category == category, cls.quality == quality))
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_item_id_by_name(cls, item_name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.id).where(cls.name == item_name)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_item_name(cls, id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.name).where(cls.id == id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def delete_item(cls, category: int, name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = delete(cls).where(and_(cls.category == category, cls.name == name))
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    def __repr__(self):
        return f'{self.id}:{self.name}:{self.type}:{self.category}:{self.quality}'


class OutputQueue(Base):
    __tablename__ = 'queue'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    item_id = Column(Integer)
    photo = Column(String)
    create_time = Column(Integer, default=datetime.datetime.now().timestamp())
    user_nickname = Column(String)
    worker = Column(BigInteger, default=0)
    gold = Column(Float)

    @classmethod
    async def add_to_queue(cls, user_id: int, item_id: int, photo: str, user_nickname: str, gold: int,
                           session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(user_id=user_id, item_id=item_id, photo=photo,
                                     user_nickname=user_nickname, gold=gold)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_user_requests(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.count(cls.id)).where(and_(cls.user_id == user_id, cls.worker == 0))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_all_queue(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.user_id, cls.gold).where(cls.worker == 0)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_first_free_queue(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.worker == 0)
            result = await db_session.execute(sql)
            return result.first()

    @classmethod
    async def get_all_free_queue(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.worker == 0)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def set_worker(cls, worker_id: int, id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(cls.id == id).values({'worker': worker_id})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def delete_from_queue(cls, id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = delete(cls).where(cls.id == id)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def is_active(cls, worker_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.worker == worker_id)
            result = await db_session.execute(sql)
            return True if result.first() else False

    @classmethod
    async def taken_ticket(cls, worker_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.worker == worker_id)
            result = await db_session.execute(sql)
            return result.first()

    def __repr__(self):
        return f'{self.id}:{self.user_id}:{self.gold}:{self.photo}:{self.item_id}:{self.user_nickname}'


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)

        print(await OutputQueue.is_active(worker_id=5667987919, session_maker=session))


    asyncio.run(main())
