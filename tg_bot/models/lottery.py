import datetime

from sqlalchemy import String, Column, Integer, insert, select, Boolean, func, and_, BigInteger
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
    user_id = Column(BigInteger)
    ticket_id = Column(Integer)
    bet = Column(Integer)
    win = Column(Integer)
    unix_date = Column(Integer, default=datetime.datetime.now().timestamp())
    date = Column(String, default=(datetime.datetime.now()).strftime('%d.%m.%Y'))

    @classmethod
    async def get_last_ticket_game(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.max(cls.id))
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def add_game(cls, user_id: int, ticket_id: int,
                       bet: int, win: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            id = await cls.get_last_ticket_game(session_maker)
            sql = insert(cls).values(
                id=id + 1 if id else 1,
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

    @classmethod
    async def get_count_games_period(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.count(cls.id))
            else:
                sql = select(func.count(cls.id)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_sum_win_period(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.win))
            else:
                sql = select(func.sum(cls.win)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_sum_bets_period(cls, date: str, session_maker: sessionmaker):
        async with session_maker() as db_session:
            if date == 'all':
                sql = select(func.sum(cls.bet))
            else:
                sql = select(func.sum(cls.bet)).where(cls.date == date)
            result = await db_session.execute(sql)
            return result.scalar()
