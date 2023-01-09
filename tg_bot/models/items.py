import datetime

from sqlalchemy import Column, Integer, String, Time

from tg_bot.services.db_base import Base


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(Integer)
    category = Column(Integer)
    quality = Column(Integer)
    create_time = Column(Time, default=datetime.datetime.now().timestamp())

    def __repr__(self):
        return f'{self.id}:{self.name}:{self.type}:{self.category}:{self.quality}'
