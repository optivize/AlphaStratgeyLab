from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime
from core.config import settings
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# We'll use the WatchlistItem class model instead of a Table

# User model
class User(Base, UserMixin):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    backtests = relationship("BacktestRecord", back_populates="user")
    watchlist = relationship("WatchlistItem")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def add_to_watchlist(self, symbol):
        item = WatchlistItem(user_id=self.id, symbol=symbol)
        return item
    
    def __repr__(self):
        return f'<User {self.username}>'

# Watchlist item model
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    symbol = Column(String, primary_key=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="watchlist")
    
    def __repr__(self):
        return f'<WatchlistItem {self.symbol} for user {self.user_id}>'

# Database models
class BacktestRecord(Base):
    __tablename__ = "backtest_records"
    
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    request = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    results = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="backtests")

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
