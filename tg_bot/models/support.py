import datetime

from sqlalchemy import Integer, Column, String, BigInteger, insert, update, select, and_, or_, func
from sqlalchemy.orm import sessionmaker

from tg_bot.services.db_base import Base


class Tickets(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    message = Column(String)
    support_id = Column(BigInteger, default=0)
    status = Column(Integer, default=0)
    date = Column(String)
    date_done = Column(String, default=None)

    @classmethod
    async def add_ticket(cls, user_id: int, message: str, date: datetime, session_maker: sessionmaker):
        async with session_maker() as db_session:
            admin_date = date.strftime('%d.%m.%Y')
            id = await cls.get_last_ticket(session_maker) + 1
            sql = insert(cls).values(id=id + 1 if id else 1, user_id=user_id, message=message, date=admin_date)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_last_ticket(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

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
    async def update_support_id(cls, ticket_id: int, support_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(cls.id == ticket_id).values({'support_id': support_id})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_available_ticket(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(and_(cls.status == 0, cls.support_id == 0))
            result = await db_session.execute(sql)
            return result.first()

    @classmethod
    async def is_active(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(and_(cls.user_id == user_id, cls.status == 0))
            result = await db_session.execute(sql)
            return False if result.first() else True

    @classmethod
    async def get_ticket_id_by_user_id(cls, first_id: int, second_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.id).where(
                and_(or_(cls.support_id == first_id, cls.support_id == second_id), cls.status == 1))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_support_id(cls, ticket_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.support_id).where(cls.id == ticket_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def support_in_dialog(cls, support_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.status).where(and_(cls.support_id == support_id, cls.status == 0))
            result = await db_session.execute(sql)
            return True if result.first() else False

    @classmethod
    async def get_queue_tickets(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.count(cls.id)).where(and_(cls.status == 0, cls.support_id == 0))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_cancel_support_tickets(cls, support_id: int, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.count(cls.id)).where(
                and_(cls.status == -2, cls.support_id == support_id, cls.date_done == date))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_done_support_tickets(cls, support_id: int, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.count(cls.id)).where(
                and_(cls.status == -1, cls.support_id == support_id, cls.date_done == date))
            result = await db_session.execute(sql)
            return result.scalar()

    def __repr__(self):
        return f'{self.id}:{self.user_id}:{self.message}:{self.date}'


class SupportBan(Base):
    __tablename__ = 'supportban'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    count = Column(Integer)
    bans = Column(Integer, default=0)
    ban_time = Column(Integer, default=0)

    @classmethod
    async def get_user(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.user_id == user_id)
            result = await db_session.execute(sql)
            return True if result.first() else False

    @classmethod
    async def get_user_warns(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.count).where(cls.user_id == user_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_user_bans(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.bans).where(cls.user_id == user_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_user_bantime(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.ban_time).where(cls.user_id == user_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def add_ban(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if await SupportBan.get_user(user_id, session_maker=session_maker):
                warns = await SupportBan.get_user_warns(user_id=user_id, session_maker=session_maker) + 1
                if warns in (3, 6, 9, 12):
                    result = {
                        3: (1, (datetime.datetime.now() + datetime.timedelta(days=1)).timestamp()),
                        6: (2, (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()),
                        9: (3, (datetime.datetime.now() + datetime.timedelta(days=30)).timestamp()),
                        12: (4, 0)
                    }
                    sql = update(cls).where(cls.user_id == user_id).values({'count': cls.count + 1,
                                                                            'bans': result[warns][0],
                                                                            'ban_time': result[warns][1]})
                else:
                    sql = update(cls).where(cls.user_id == user_id).values({'count': cls.count + 1})
            else:
                id = await cls.get_last_supportban(session_maker)
                sql = insert(cls).values(id=id + 1 if id else 1, user_id=user_id, count=1)

            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_last_supportban(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_warns_by_date(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.count(cls.id))
            else:
                unix_date = datetime.datetime.strptime(date, '%d.%m.%Y')
                days_30 = ((unix_date + datetime.timedelta(days=8)).timestamp(),
                           (unix_date + datetime.timedelta(days=31)).timestamp())
                days_7 = ((unix_date + datetime.timedelta(days=2)).timestamp(),
                          (unix_date + datetime.timedelta(days=8)).timestamp())
                days_1 = (unix_date.timestamp(),
                          (unix_date + datetime.timedelta(days=2)).timestamp())
                sql = select(func.count(cls.id)).where(or_(and_(cls.ban_time > days_1[0], cls.ban_time < days_1[1]),
                                                           and_(cls.ban_time > days_7[0], cls.ban_time < days_7[1]),
                                                           and_(cls.ban_time > days_30[0], cls.ban_time < days_30[1])))
            result = await db_session.execute(sql)
            return result.scalar()
