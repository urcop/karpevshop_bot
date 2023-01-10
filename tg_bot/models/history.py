import asyncio
import datetime

from sqlalchemy import Column, Integer, BigInteger, String, insert, select, func
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class GoldHistory(Base):
    __tablename__ = 'gold_history'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    gold = Column(Integer)
    unix_date = Column(BigInteger, default=datetime.datetime.now().timestamp())
    date = Column(String, default=datetime.datetime.now().strftime('%d.%m.%Y'))

    @classmethod
    async def add_gold_purchase(cls, session_maker: sessionmaker, telegram_id: int,
                                gold: int):
        async with session_maker() as db_session:
            sql = insert(cls).values(telegram_id=telegram_id, gold=gold)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_count_user_purchase(cls, session_maker: sessionmaker, telegram_id: int):
        async with session_maker() as db_session:
            sql = select(func.count(cls.telegram_id)).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            return result.scalar()

    def __repr__(self):
        return f'{self.id}:{self.date}:{self.unix_date}'


class BalanceHistory(Base):
    __tablename__ = 'balance_history'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    balance = Column(Integer)
    unix_date = Column(BigInteger, default=datetime.datetime.now().timestamp())
    date = Column(String, default=datetime.datetime.now().strftime('%d.%m.%Y'))

    @classmethod
    async def add_balance_purchase(cls, session_maker: sessionmaker, telegram_id: int,
                                   money: int):
        async with session_maker() as db_session:
            sql = insert(cls).values(telegram_id=telegram_id, balance=money)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

