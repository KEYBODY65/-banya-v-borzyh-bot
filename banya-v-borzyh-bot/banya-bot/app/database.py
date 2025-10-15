from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String(100))
    first_name = Column(String(100))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)

class WaitingList(Base):
    __tablename__ = 'waiting_list'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    preferred_dates = Column(String(200))
    people_count = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

engine = create_engine('sqlite:///banya_bot.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()