import asyncio
import datetime

from sqlalchemy import Column, Integer, String, insert, delete, update, select, func
from sqlalchemy.orm import sessionmaker

from tg_bot.config import load_config
from tg_bot.services.database import create_db_session
from tg_bot.services.db_base import Base


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    photo = Column(String, default=None)
    time_created = Column(Integer, default=datetime.datetime.now().timestamp())
    price = Column(Integer)

    @classmethod
    async def add_product(cls, name: str, description: str,
                          price: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            id = await cls.get_last_product(session_maker)
            sql = insert(cls).values(id=id + 1 if id else 1, name=name, description=description, price=price)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_last_product(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def delete_product(cls, name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            id = await cls.get_last_product(session_maker)
            sql = delete(cls).where(cls.name == name)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_id(cls, name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.id).where(cls.name == name)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def add_photo(cls, id: int, photo: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(cls.id == id).values({'photo': photo})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_all_products(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls)
            result = await db_session.execute(sql)
            return result.all()

    def __repr__(self):
        return f'{self.name}:{self.description}:{self.price}:{self.photo}'


if __name__ == '__main__':
    async def main():
        config = load_config()
        session = await create_db_session(config)

        products = await Product.get_all_products(session_maker=session)
        print(products)


    asyncio.run(main())
