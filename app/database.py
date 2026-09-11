from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = (
    "postgresql://"
    "rakshak:"
    "rakshak_dev_password"
    "@localhost:5433/"
    "rakshakcare"
)


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# DATABASE SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# BASE MODEL
# ============================================================

Base = declarative_base()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# CREATE ALL TABLES
# ============================================================

def create_tables():

    # Existing models
    from app.models.soldier import Soldier
    from app.models.wellbeing import WellbeingRecord
    from app.models.sos import SOSAlert

    # New facial analysis model
    from app.models.facial_scan import FacialScan

    # Create tables if they don't already exist
    Base.metadata.create_all(
        bind=engine
    )
