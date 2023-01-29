import datetime

from sqlalchemy import Column, Integer, BigInteger, String

from tg_bot.services.db_base import Base


class JackpotGame(Base):
    __tablename__ = 'jackpot_games'
    id = Column(Integer, primary_key=True)
    winner_id = Column(BigInteger)
    jackpot = Column(Integer)
    time_end = Column(Integer)
    active = Column(Integer)
    bot_jackpot = Column(Integer)
    date = Column(String, default=datetime.datetime.now().strftime('%d.%m.%Y'))