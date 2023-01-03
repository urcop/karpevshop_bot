import asyncio
from datetime import datetime

from sqlalchemy import BigInteger, Column, String, Integer, select, insert, func, ForeignKey, update, Date
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class User(Base):
    __tablename__ = 'users'
    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(String(length=100))
    fullname = Column(String(length=100))
    balance = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    role = Column(String(length=100), default='user')
    reg_date = Column(Date, default=datetime.now().date())

    @classmethod
    async def get_user(cls, session_maker: sessionmaker, telegram_id: int) -> 'User':
        async with session_maker() as db_session:
            sql = select(cls).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            user: cls = request.scalar()
        return user

    @classmethod
    async def add_user(cls,
                       session_maker: sessionmaker,
                       telegram_id: int,
                       fullname: str,
                       username: str = None,
                       ) -> 'User':
        async with session_maker() as db_session:
            sql = insert(cls).values(
                telegram_id=telegram_id,
                fullname=fullname,
                username=username
            ).returning('*')
            result = await db_session.execute(sql)
            await db_session.commit()
            return result.first()

    @classmethod
    async def get_balance(cls, session_maker: sessionmaker, telegram_id: int) -> int:
        async with session_maker() as db_session:
            sql = select(cls.balance).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            await db_session.commit()
            return request.scalar()

    @classmethod
    async def get_gold(cls, session_maker: sessionmaker, telegram_id: int) -> int:
        async with session_maker() as db_session:
            sql = select(cls.gold).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            await db_session.commit()
            return request.scalar()

    @classmethod
    async def add_currency(cls,
                           session_maker: sessionmaker,
                           telegram_id: int,
                           currency_type: str,
                           value: float) -> 'User':
        async with session_maker() as db_session:
            if currency_type == 'g':
                sql = update(
                    cls
                ).where(
                    cls.telegram_id == telegram_id
                ).values(
                    {'gold': cls.gold + value}
                )
            elif currency_type == 'm':
                sql = update(
                    cls
                ).where(
                    cls.telegram_id == telegram_id
                ).values(
                    {'balance': cls.balance + value}
                )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @staticmethod
    async def count_referrals(session_maker: sessionmaker, user: "User") -> int:
        async with session_maker() as db_session:
            sql = select(
                func.count(Referral.telegram_id)
            ).where(
                Referral.referrer == user.telegram_id
            ).join(
                User
            ).group_by(
                Referral.referrer
            )
            result = await db_session.execute(sql)
            return result.scalar()

    def __repr__(self):
        return f'User (ID: {self.telegram_id} - {self.fullname})'


class Referral(Base):
    __tablename__ = 'referral_users'
    telegram_id = Column(BigInteger, primary_key=True)
    referrer = Column(ForeignKey(User.telegram_id, ondelete='CASCADE'))

    @classmethod
    async def add_user(cls,
                       db_session: sessionmaker,
                       telegram_id: int,
                       referrer: int
                       ) -> 'User':
        async with db_session() as db_session:
            sql = insert(cls).values(
                telegram_id=telegram_id,
                referrer=referrer
            )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result
