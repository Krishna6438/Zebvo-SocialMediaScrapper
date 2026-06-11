import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./passport_dashboard.db")

# Standardize postgres:// to postgresql:// for SQLAlchemy 1.4+ compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True)          # twitter, reddit, facebook, instagram, linkedin, youtube, tiktok
    post_id = Column(String, unique=True, index=True) # Unique ID from the platform
    username = Column(String)
    user_handle = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    language = Column(String, default="english")
    region = Column(String, default="Global")
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    sentiment = Column(String, default="Neutral")    # Positive, Neutral, Negative
    category = Column(String, default="Personal Experiences", index=True) # Topical categories
    summary = Column(Text)
    cluster_id = Column(Integer, nullable=True, index=True) # Groups duplicate/similar posts
    is_gibberish = Column(Boolean, default=False)
    
    # Store translations as a JSON-string in the database: e.g. {"hindi": "...", "punjabi": "..."}
    translations_json = Column(Text, default="{}")

    def to_dict(self):
        """Helper to convert ORM model to dictionary."""
        return {
            "id": self.id,
            "platform": self.platform,
            "post_id": self.post_id,
            "username": self.username,
            "user_handle": self.user_handle,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "language": self.language,
            "region": self.region,
            "likes": self.likes,
            "shares": self.shares,
            "comments": self.comments,
            "sentiment": self.sentiment,
            "category": self.category,
            "summary": self.summary,
            "cluster_id": self.cluster_id,
            "is_gibberish": self.is_gibberish,
            "translations": json.loads(self.translations_json or "{}")
        }

def init_db():
    """Initializes the database tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
