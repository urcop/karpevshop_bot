from sqlalchemy import Column, String, Integer, Boolean, select, ForeignKey
from sqlalchemy.orm import sessionmaker

from tg_bot.services.db_base import Base


class Case(Base):
    __tablename__ = 'cases'
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    price = Column(Integer)
    visible = Column(Boolean)

    @classmethod
    async def get_visible_cases(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.visible)
            result = await db_session.execute(sql)
            return result.all()

    def __repr__(self):
        return f'{self.id}:{self.name}:{self.price}'


class CaseItems(Base):
    __tablename__ = 'case_items'
    id = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey(Case.id, ondelete='CASCADE'))
    name = Column(String(120))
    game_price = Column(Integer)
    chance = Column(Integer)

    @classmethod
    async def get_items_case_id(cls, case_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.case_id == case_id)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_chances_items(cls, case_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.chance).where(cls.case_id == case_id)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_names_items(cls, case_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.name).where(cls.case_id == case_id)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_price_item(cls, item_name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.game_price).where(cls.name == item_name)
            result = await db_session.execute(sql)
            return result.scalar()

    def __repr__(self):
        return f'{self.id}:{self.case_id}:{self.name}:{self.game_price}:{self.chance}'
