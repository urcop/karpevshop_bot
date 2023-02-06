import datetime

from sqlalchemy import Column, String, Integer, Boolean, select, ForeignKey, BigInteger, insert, update, delete
from sqlalchemy.orm import sessionmaker

from tg_bot.services.db_base import Base


class Case(Base):
    __tablename__ = 'cases'
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    price = Column(Integer)
    visible = Column(Boolean, default=False)

    @classmethod
    async def add_case(cls, name: str, price: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(name=name, price=price)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def delete_case(cls, name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = delete(cls).where(cls.name == name)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_case_id(cls, name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.id).where(cls.name == name)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_case_name(cls, id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.name).where(cls.id == id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_visible_cases(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.visible)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def change_visible(cls, case_id: int, visible: bool, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(cls.id == case_id).values({'visible': visible})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    def __repr__(self):
        return f'{self.id}:{self.name}:{self.price}'


class FreeCaseCooldown(Base):
    __tablename__ = 'free_case_cooldown'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    cooldown_time = Column(BigInteger)

    @classmethod
    async def add_user_cooldown(cls, date: datetime, session_maker: sessionmaker, telegram_id: int) -> 'FreeCaseCooldown':
        async with session_maker() as db_session:
            unix_date = int(date.timestamp())
            sql = insert(cls).values(telegram_id=telegram_id, cooldown_time=unix_date)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def is_exists(cls, telegram_id: int, session_maker: sessionmaker) -> bool:
        async with session_maker() as db_session:
            sql = select(cls).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            return True if result.scalar() else False

    @classmethod
    async def is_active(cls, session_maker: sessionmaker, telegram_id: int):
        async with session_maker() as db_session:
            sql = select(cls.cooldown_time).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            return True if result.scalar() - datetime.datetime.now().timestamp() <= 0 else False

    @classmethod
    async def get_remaining_time(cls, session_maker: sessionmaker, telegram_id: int):
        async with session_maker() as db_session:
            sql = select(cls.cooldown_time).where(cls.telegram_id == telegram_id)
            result = await db_session.execute(sql)
            remaining_time = datetime.datetime.fromtimestamp(result.scalar()) - datetime.datetime.now()
            return str(remaining_time).replace('days', 'дней').replace('day', 'день').split('.')[0]

    @classmethod
    async def add_cooldown(cls, session_maker: sessionmaker, telegram_id: int):
        async with session_maker() as db_session:
            days = (datetime.datetime.now() + datetime.timedelta(days=3)).timestamp()
            sql = update(
                cls
            ).where(
                cls.telegram_id == telegram_id
            ).values(
                {"cooldown_time": days}
            )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    def __repr__(self):
        return f'{self.id}:{self.telegram_id}:{self.cooldown_time}'


class CaseItems(Base):
    __tablename__ = 'case_items'
    id = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey(Case.id, ondelete='CASCADE'))
    name = Column(String(120))
    game_price = Column(Integer)
    chance = Column(Integer)

    @classmethod
    async def add_case_item(cls, case_id: int, game_price: int, chance: int, item_name: str,
                            session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(case_id=case_id, game_price=game_price, chance=chance, name=item_name)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def delete_case_item(cls, item_name: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = delete(cls).where(cls.name == item_name)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

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
