import asyncio

from sqlalchemy import String, Column, Integer, insert, select, update, BigInteger, and_
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class Promocode(Base):
    __tablename__ = 'promocode'
    id = Column(Integer, primary_key=True)
    code_name = Column(String(length=100))
    currency = Column(String(length=1))
    count_use = Column(Integer)
    value = Column(Integer)

    @classmethod
    async def create_promo(cls,
                           session_maker: sessionmaker,
                           code_name: str,
                           currency: str,
                           count_use: int,
                           value: int) -> 'Promocode':
        async with session_maker() as db_session:
            sql = insert(cls).values(
                code_name=code_name,
                currency=currency,
                count_use=count_use,
                value=value,
            )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result.first()

    @classmethod
    async def get_promo(cls, code_name: str, session_maker: sessionmaker) -> bool:
        async with session_maker() as db_session:
            sql = select(cls).where(code_name == cls.code_name)
            result = await db_session.execute(sql)
            return True if result.first() else False

    @classmethod
    async def get_promo_type(cls, code_name: str, session_maker: sessionmaker) -> str:
        async with session_maker() as db_session:
            sql = select(cls.currency).where(code_name == cls.code_name)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_promo_value(cls, code_name: str, session_maker: sessionmaker) -> int:
        async with session_maker() as db_session:
            sql = select(cls.value).where(code_name == cls.code_name)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def is_active(cls, code_name: str, session_maker: sessionmaker) -> bool:
        async with session_maker() as db_session:
            sql = select(cls.count_use).where(code_name == cls.code_name)
            result = await db_session.execute(sql)
            return True if int(result.first()[0]) > 0 else False

    @classmethod
    async def decrement(cls, code_name: str, session_maker: sessionmaker) -> 'Promocode':
        async with session_maker() as db_session:
            sql = update(
                cls
            ).where(
                cls.code_name == code_name
            ).values(
                {'count_use': cls.count_use - 1}
            )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_id(cls, code_name: str, session_maker: sessionmaker) -> int:
        async with session_maker() as db_session:
            sql = select(cls.id).where(cls.code_name == code_name)
            result = await db_session.execute(sql)
            return result.scalar()

    def __repr__(self):
        return f'Promo (ID: {self.id} - {self.code_name})'


class User2Promo(Base):
    __tablename__ = 'user2promo'
    id = Column(Integer, primary_key=True)
    promo_id = Column(Integer)
    user_id = Column(BigInteger)

    @classmethod
    async def add_user_promo(cls, user_id: int, promo_id: int, session_maker: sessionmaker) -> 'User2Promo':
        async with session_maker() as db_session:
            sql = insert(cls).values(user_id=user_id, promo_id=promo_id)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_user_promo(cls, user_id: int, promo_id: int, session_maker: sessionmaker) -> bool:
        async with session_maker() as db_session:
            sql = select(cls).where(and_(cls.user_id == user_id, cls.promo_id == promo_id))
            result = await db_session.execute(sql)
            return True if result.first() else False

    def __repr__(self):
        return f'User2Promo - {self.user_id}, {self.promo_id}'


if __name__ == '__main__':
    async def test():
        config = load_config()
        session_maker = await create_db_session(config)
        user2promo = await Promocode.get_id(code_name='hui', session_maker=session_maker)
        print(user2promo)


    asyncio.run(test())
