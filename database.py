from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = "sqlite:///./esewa_reviews.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String, unique=True, index=True)
    platform = Column(String, index=True)           # "playstore" or "appstore"
    user_name = Column(String)
    rating = Column(Float)
    text = Column(Text)
    sentiment = Column(String)                      # "positive", "neutral", "negative"
    sentiment_score = Column(Float)
    app_version = Column(String, nullable=True)
    review_date = Column(DateTime)
    scrape_date = Column(DateTime, default=datetime.utcnow)
    thumbs_up = Column(Integer, default=0)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
