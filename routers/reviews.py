from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db, Review
from scraper import android as play_scraper
from scraper import ios as app_scraper
from datetime import datetime
from typing import Optional
import asyncio

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def _upsert_reviews(db: Session, reviews_data: list[dict]):
    """Insert new reviews, skip if already exists."""
    new_count = 0
    for r in reviews_data:
        existing = db.query(Review).filter(Review.review_id == r["review_id"]).first()
        if not existing:
            rev = Review(**r)
            db.add(rev)
            new_count += 1
    db.commit()
    return new_count


def _serialize(review: Review) -> dict:
    return {
        "id": review.id,
        "review_id": review.review_id,
        "platform": review.platform,
        "user_name": review.user_name,
        "rating": review.rating,
        "text": review.text,
        "sentiment": review.sentiment,
        "sentiment_score": review.sentiment_score,
        "app_version": review.app_version,
        "review_date": review.review_date.isoformat() if review.review_date else None,
        "thumbs_up": review.thumbs_up,
    }


@router.post("/playstore/scrape")
def scrape_playstore(
    count: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """Scrape the latest Play Store reviews and persist to DB."""
    data = play_scraper.fetch_reviews(count=count)
    new = _upsert_reviews(db, data)
    return {"scraped": len(data), "new_records": new, "platform": "playstore"}


@router.post("/appstore/scrape")
def scrape_appstore(
    count: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """Scrape the latest App Store reviews and persist to DB."""
    data = app_scraper.fetch_reviews(count=count)
    new = _upsert_reviews(db, data)
    return {"scraped": len(data), "new_records": new, "platform": "appstore"}


@router.get("/playstore")
def get_playstore_reviews(
    sentiment: Optional[str] = None,
    rating: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Review).filter(Review.platform == "playstore")
    if sentiment:
        q = q.filter(Review.sentiment == sentiment)
    if rating:
        q = q.filter(Review.rating == rating)
    if search:
        q = q.filter(Review.text.ilike(f"%{search}%"))
    total = q.count()
    items = q.order_by(Review.review_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serialize(r) for r in items],
    }


@router.get("/appstore")
def get_appstore_reviews(
    sentiment: Optional[str] = None,
    rating: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Review).filter(Review.platform == "appstore")
    if sentiment:
        q = q.filter(Review.sentiment == sentiment)
    if rating:
        q = q.filter(Review.rating == rating)
    if search:
        q = q.filter(Review.text.ilike(f"%{search}%"))
    total = q.count()
    items = q.order_by(Review.review_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serialize(r) for r in items],
    }


@router.get("/recent")
def get_recent_reviews(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    items = db.query(Review).order_by(Review.scrape_date.desc()).limit(limit).all()
    return [_serialize(r) for r in items]
