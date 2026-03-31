from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, Review

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """Aggregate metrics for the dashboard overview cards."""
    total = db.query(Review).count()
    total_play = db.query(Review).filter(Review.platform == "playstore").count()
    total_app = db.query(Review).filter(Review.platform == "appstore").count()

    avg_rating = db.query(func.avg(Review.rating)).scalar() or 0.0
    avg_play = db.query(func.avg(Review.rating)).filter(Review.platform == "playstore").scalar() or 0.0
    avg_app = db.query(func.avg(Review.rating)).filter(Review.platform == "appstore").scalar() or 0.0

    def sentiment_counts(platform=None):
        q = db.query(Review.sentiment, func.count(Review.id))
        if platform:
            q = q.filter(Review.platform == platform)
        rows = q.group_by(Review.sentiment).all()
        d = {s: c for s, c in rows}
        total_sent = sum(d.values()) or 1
        return {
            "positive": d.get("positive", 0),
            "neutral": d.get("neutral", 0),
            "negative": d.get("negative", 0),
            "positive_pct": round(d.get("positive", 0) / total_sent * 100, 1),
            "neutral_pct": round(d.get("neutral", 0) / total_sent * 100, 1),
            "negative_pct": round(d.get("negative", 0) / total_sent * 100, 1),
        }

    return {
        "total_reviews": total,
        "total_playstore": total_play,
        "total_appstore": total_app,
        "avg_rating": round(avg_rating, 2),
        "avg_rating_playstore": round(avg_play, 2),
        "avg_rating_appstore": round(avg_app, 2),
        "sentiment_overall": sentiment_counts(),
        "sentiment_playstore": sentiment_counts("playstore"),
        "sentiment_appstore": sentiment_counts("appstore"),
    }


@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    """Monthly sentiment trends for the line chart."""
    rows = db.query(
        func.strftime("%Y-%m", Review.review_date).label("month"),
        Review.sentiment,
        func.count(Review.id).label("count"),
    ).group_by("month", Review.sentiment).order_by("month").all()

    months = {}
    for month, sentiment, count in rows:
        if month not in months:
            months[month] = {"month": month, "positive": 0, "neutral": 0, "negative": 0}
        months[month][sentiment] = count

    return list(months.values())
