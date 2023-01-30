import datetime

from sqlalchemy import Column, Integer, BigInteger, String, insert, select, func, update
from sqlalchemy.orm import sessionmaker

from tg_bot.services.db_base import Base


class JackpotGame(Base):
    __tablename__ = 'jackpot_games'
    id = Column(Integer, primary_key=True)
    winner_id = Column(BigInteger)
    jackpot = Column(Integer)
    time_end = Column(Integer, default=(datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp())
    active = Column(Integer)
    bot_jackpot = Column(Integer)
    date = Column(String, default=datetime.datetime.now().strftime('%d.%m.%Y'))

    @classmethod
    async def create_room(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(active=1)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def check_available_room(cls, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.id).where(cls.active == 1)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_end_time(cls, room_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.time_end).where(cls.id == room_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def update_active_room(cls, room_id: int, status: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(cls.id == room_id).values({'active': status})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def update_params_room(cls, room_id: int, winner_id, jackpot, bot_jackpot, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = update(cls).where(cls.id == room_id).values({'winner_id': winner_id,
                                                               'jackpot': jackpot,
                                                               'bot_jackpot': bot_jackpot})
            result = await db_session.execute(sql)
            await db_session.commit()
            return result


class JackpotBets(Base):
    __tablename__ = 'jackpot_bets'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    room_id = Column(Integer)
    bet = Column(Integer)

    @classmethod
    async def add_bet(cls, user_id: int, room_id: int, bet: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = insert(cls).values(user_id=user_id, room_id=room_id, bet=bet)
            result = await db_session.execute(sql)
            await db_session.commit()
            return result

    @classmethod
    async def get_users(cls, room_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(cls.user_id, func.sum(cls.bet)
                         ).where(cls.room_id == room_id
                                 ).group_by(cls.user_id
                                            ).order_by(func.sum(cls.bet).desc())
            result = await db_session.execute(sql)
            return result.all()

    @classmethod
    async def get_user_bet(cls, room_id: int, user_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.sum(cls.bet)).where(cls.room_id == room_id, cls.user_id == user_id)
            result = await db_session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_sum_bets(cls, room_id: int, session_maker: sessionmaker):
        async with session_maker() as db_session:
            sql = select(func.sum(cls.bet)).where(cls.room_id == room_id)
            result = await db_session.execute(sql)
            return result.scalar()
