from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean

from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, time

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String(100))
    first_name = Column(String(100))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)

class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    booking_date = Column(DateTime)
    service = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)    

engine = create_engine('sqlite:///banya_bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()