import asyncio
from datetime import datetime

from sqlalchemy import BigInteger, Column, String, Integer, select, insert, func, ForeignKey, update, delete
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
    reg_date = Column(String)

    @classmethod
    async def delete_user(cls, session_maker: sessionmaker, telegram_id: int):
        async with session_maker() as db_session:
            sql = delete(cls).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_user(cls, session_maker: sessionmaker, telegram_id: int) -> 'User':
        async with session_maker() as db_session:
            sql = select(cls).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            user: cls = request.scalar()
        return user

    @classmethod
    async def get_all_users(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.telegram_id)
            request = await db_session.execute(sql)
            return request.all()

    @classmethod
    async def add_user(cls,
                       session_maker: sessionmaker,
                       telegram_id: int,
                       fullname: str,
                       date: datetime,
                       username: str = None,
                       ) -> 'User':
        async with session_maker() as db_session:
            admin_date = date.strftime('%d.%m.%Y')
            sql = insert(cls).values(
                telegram_id=telegram_id,
                fullname=fullname,
                username=username,
                reg_date=admin_date
            ).returning('*')
            result = await db_session.execute(sql)
            await db_session.commit()
            return result.first()

    @classmethod
    async def update_username_fullname(cls, telegram_id: int, session_maker: sessionmaker, username: str,
                                       fullname: str) -> 'User':
        async with session_maker() as db_session:
            extra_context = {'username': username, 'fullname': fullname}
            sql = update(cls).where(cls.telegram_id == telegram_id).values(extra_context)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_balance(cls, session_maker: sessionmaker, telegram_id: int) -> int:
        async with session_maker() as db_session:
            sql = select(cls.balance).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            return request.scalar()

    @classmethod
    async def get_gold(cls, session_maker: sessionmaker, telegram_id: int) -> int:
        async with session_maker() as db_session:
            sql = select(cls.gold).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            return request.scalar()

    @classmethod
    async def add_currency(cls,
                           session_maker: sessionmaker,
                           telegram_id: int,
                           currency_type: str,
                           value: [int, float]) -> 'User':
        async with session_maker() as db_session:
            extra_context = {currency_type: cls.gold + value if currency_type == 'gold' else cls.balance + value}
            sql = update(cls).where(cls.telegram_id == telegram_id).values(extra_context)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_users_by_reg_date(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.count(cls.telegram_id))
            else:
                sql = select(func.count(cls.telegram_id)).where(cls.reg_date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_users_id_by_reg_date(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(cls.telegram_id)
            else:
                sql = select(cls.telegram_id).where(cls.reg_date == date)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def take_currency(cls,
                            session_maker: sessionmaker,
                            telegram_id: int,
                            currency_type: str,
                            value: int) -> 'User':
        async with session_maker() as db_session:
            extra_context = {currency_type: cls.gold - value if currency_type == 'gold' else cls.balance - value}
            sql = update(cls).where(cls.telegram_id == telegram_id).values(extra_context)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_admins(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.telegram_id).where(cls.role == 'admin')
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_workers(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.telegram_id).where(cls.role == 'worker')
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_supports(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.telegram_id).where(cls.role == 'support')
            result = await db_session.execute(sql)
            return result.all()

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

    @classmethod
    async def is_enough(cls, session_maker: sessionmaker, telegram_id: int,
                        currency_type: str, count: int):
        async with session_maker() as db_session:
            if currency_type == 'balance':
                sql = select(cls.balance).where(telegram_id == cls.telegram_id)
            elif currency_type == 'gold':
                sql = select(cls.gold).where(telegram_id == cls.telegram_id)
            result = await db_session.execute(sql)
            return True if result.scalar() >= count else False

    @classmethod
    async def set_role(cls, user_id: int, role: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(user_id == cls.telegram_id).values({'role': role})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_reg_date(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.reg_date).where(user_id == cls.telegram_id)
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

    @classmethod
    async def get_referrer(cls, telegram_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.referrer).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_referrals(cls, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.telegram_id).where(cls.referrer == user_id)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_user(cls, session_maker: sessionmaker, user_id: int):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.telegram_id == user_id)
            result = await db_session.execute(sql)
            return True if result.first() else False


if __name__ == '__main__':
    async def blabla():
        config = load_config()
        session_maker = await create_db_session(config)

        print(await Referral.get_referrals(383212537, session_maker))


    asyncio.run(blabla())
