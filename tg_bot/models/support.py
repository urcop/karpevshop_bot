import datetime

from sqlalchemy import Integer, Column, String, BigInteger, insert, update, select, and_
from sqlalchemy.orm import sessionmaker

from tg_bot.services.db_base import Base


class Tickets(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    message = Column(String)
    support_id = Column(BigInteger, default=None)
    status = Column(Integer, default=0)
    date = Column(String, default=datetime.datetime.now().strftime('%d.%m.%Y'))
    date_done = Column(String, default=None)

    @classmethod
    async def add_ticket(cls, user_id: int, message: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(user_id=user_id, message=message)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def update_status(cls, ticket_id: int, status: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            now_date = datetime.datetime.now().strftime('%d.%m.%Y')
            sql = update(cls).where(cls.id == ticket_id).values({'status': status,
                                                                 'date_done': now_date})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def update_status_by_user(cls, support_id: int, status: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            now_date = datetime.datetime.now().strftime('%d.%m.%Y')
            sql = update(cls).where(and_(cls.support_id == support_id, cls.status == 1)).values({'status': status,
                                                                                                 'date_done': now_date})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def update_support_id(cls, ticket_id: int, support_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(cls.id == ticket_id).values({'support_id': support_id})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_available_ticket(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.status == 0)
            result = await db_session.execute(sql)
            return result.first()

    @classmethod
    async def is_active(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(and_(cls.user_id == user_id, cls.status == 0))
            result = await db_session.execute(sql)
            return False if result.first() else True

    def __repr__(self):
        return f'{self.id}:{self.user_id}:{self.message}:{self.date}'
