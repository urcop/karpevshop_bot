import datetime

from sqlalchemy import String, Column, Integer, insert, select, Boolean, func, and_
from sqlalchemy.orm import sessionmaker

from tg_bot.services.db_base import Base


class LotteryTickets(Base):
    __tablename__ = 'lottery_tickets'
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    price = Column(Integer)
    visible = Column(Boolean)
    max_win = Column(Integer)
    min_win = Column(Integer, default=0)

    @classmethod
    async def add_lottery_ticket(cls, name: str, price: int, max_win: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(
                name=name,
                price=price,
                max_win=max_win
            )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_all_lottery_tickets(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.visible)
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_ticket(cls, id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls).where(cls.id == id)
            result = await db_session.execute(sql)
            return result.scalar()

    def __repr__(self):
        return f'{self.id}:{self.name}:{self.price}:{self.max_win}:{self.min_win}'


class TicketGames(Base):
    __tablename__ = 'ticket_games'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    ticket_id = Column(Integer)
    bet = Column(Integer)
    win = Column(Integer)
    unix_date = Column(Integer, default=datetime.datetime.now().timestamp())
    date = Column(String, default=(datetime.datetime.now()).strftime('%d.%m.%Y'))

    @classmethod
    async def add_game(cls, user_id: int, ticket_id: int,
                       bet: int, win: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(
                user_id=user_id,
                ticket_id=ticket_id,
                bet=bet,
                win=win
            )
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_count_games(cls, user_id: int, ticket_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.count(cls.user_id)).where(and_(cls.ticket_id == ticket_id, cls.user_id == user_id))
            result = await db_session.execute(sql)
            return result.scalar()
