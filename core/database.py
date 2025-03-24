from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class BacktestRecord(Base):
    __tablename__ = "backtest_records"
    
    id = Column(String, primary_key=True)
    request = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    results = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

class CustomData(Base):
    __tablename__ = "custom_data_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    symbols_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """
    Initialize database tables
    """
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependency for database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database on import
init_db()
