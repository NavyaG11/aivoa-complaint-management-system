"""
Database setup.

Uses SQLite by default so you can run the whole project with zero
extra setup. Swap DATABASE_URL in .env for a MySQL/Postgres URL later —
nothing else in this file needs to change since SQLAlchemy abstracts it.
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")

# check_same_thread is only needed for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_source = Column(String(255))
    customer_name = Column(String(255))
    product_name = Column(String(255))
    product_strength = Column(String(255))
    batch_number = Column(String(255))
    manufacturing_date = Column(String(64))
    expiry_date = Column(String(64))
    quantity_affected = Column(String(64))
    complaint_type = Column(String(255))
    complaint_date = Column(String(64))
    description = Column(Text)
    initial_severity = Column(String(64))
    priority = Column(String(64))
    possible_duplicate = Column(String(8), default="false")  # "true"/"false" - simple flag from the duplicate-check node
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
