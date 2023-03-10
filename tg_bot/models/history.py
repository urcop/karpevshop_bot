import asyncio
import datetime

from sqlalchemy import Column, Integer, BigInteger, String, insert, select, func, and_
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class GoldHistory(Base):
    __tablename__ = 'gold_history'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    gold = Column(Integer)
    unix_date = Column(BigInteger)
    date = Column(String)

    @classmethod
    async def get_last_gh(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def add_gold_purchase(cls, session_maker: sessionmaker, telegram_id: int,
                                gold: int, date: datetime):
        async with session_maker() as db_session:
            unix_date = int(date.timestamp())
            admin_date = date.strftime('%d.%m.%Y')
            id = await cls.get_last_gh(session_maker)
            sql = insert(cls).values(id=id + 1 if id else 1, telegram_id=telegram_id, gold=gold,
                                     unix_date=unix_date, date=admin_date)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_sum_user_purchase(cls, session_maker: sessionmaker, telegram_id: int):
        async with session_maker() as db_session:
            sql = select(func.sum(cls.gold)).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_count_user_purchase(cls, session_maker: sessionmaker, telegram_id: int):
        async with session_maker() as db_session:
            sql = select(func.count(cls.gold)).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_history_period(cls, session_maker: sessionmaker, start_time: int, end_time: int):
        async with session_maker() as db_session:
            sql = select(
                cls.telegram_id, func.sum(cls.gold)
            ).where(
                and_(cls.unix_date <= end_time, cls.unix_date >= start_time)
            ).group_by(
                cls.telegram_id
            ).order_by(
                func.sum(cls.gold).desc()
            )
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_stats_params(cls, session_maker: sessionmaker, date: str):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.gold))
            else:
                sql = select(func.sum(cls.gold)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_gold_user_period(cls, session_maker: sessionmaker, start_time: int, end_time: int, user_id: int):
        async with session_maker() as db_session:
            sql = select(
                func.sum(cls.gold)
            ).where(
                and_(cls.unix_date <= end_time, cls.unix_date >= start_time, cls.telegram_id == user_id)
            )
            result = await db_session.execute(sql)
            return result.scalar()

    def __repr__(self):
        return f'{self.id}:{self.date}:{self.unix_date}'


class BalanceHistory(Base):
    __tablename__ = 'balance_history'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    balance = Column(Integer)
    unix_date = Column(BigInteger)
    date = Column(String)

    @classmethod
    async def get_last_bh(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def add_balance_purchase(cls, session_maker: sessionmaker, telegram_id: int,
                                   money: int, date: datetime):
        unix_date = int(date.timestamp())
        admin_date = date.strftime('%d.%m.%Y')
        async with session_maker() as db_session:
            id = await cls.get_last_bh(session_maker)
            sql = insert(cls).values(id=id + 1 if id else 1, telegram_id=telegram_id, balance=money,
                                     unix_date=unix_date, date=admin_date)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_stats_params(cls, session_maker: sessionmaker, date: str):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.balance))
            else:
                sql = select(func.sum(cls.balance)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()


class CaseHistory(Base):
    __tablename__ = 'case_history'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    gold_won = Column(Integer)
    money_spent = Column(Integer)
    unix_date = Column(BigInteger)
    date = Column(String)

    @classmethod
    async def get_last_ch(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def add_case_open(cls, session_maker: sessionmaker, telegram_id: int,
                            gold_won: int, money_spent: int, date: datetime):
        async with session_maker() as db_session:
            unix_date = int(date.timestamp())
            admin_date = date.strftime('%d.%m.%Y')
            id = await cls.get_last_ch(session_maker)
            sql = insert(cls).values(id=id + 1 if id else 1, telegram_id=telegram_id, gold_won=gold_won,
                                     money_spent=money_spent, unix_date=unix_date, date=admin_date)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_case_stats_gold(cls, session_maker: sessionmaker, date: str):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.gold_won))
            else:
                sql = select(func.sum(cls.gold_won)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_case_stats_money(cls, session_maker: sessionmaker, date: str):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.money_spent))
            else:
                sql = select(func.sum(cls.money_spent)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_case_stats_opened(cls, session_maker: sessionmaker, date: str):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.count(cls.id))
            else:
                sql = select(func.count(cls.id)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)
        summary_gold = [await GoldHistory.get_stats_params(session, date) for date in ['01.02.2023', '31.01.2023']]

        print(sum(summary_gold))


    asyncio.run(main())
