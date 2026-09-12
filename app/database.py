import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rakshak:rakshak_dev_password@localhost:5433/rakshakcare"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import models before create_all so SQLAlchemy knows all tables.
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord
from app.models.sos import SOSAlert
from app.models.facial_scan import FacialScan


# Create tables if they don't already exist.
Base.metadata.create_all(bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)
