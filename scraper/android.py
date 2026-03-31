from google_play_scraper import reviews, Sort
from datetime import datetime
from sentiment.analyzer import analyze
import hashlib


ESEWA_PACKAGE = "com.f1soft.esewa"


def _make_id(review: dict, platform: str) -> str:
    raw = f"{platform}-{review.get('reviewId', review.get('userName',''))}"
    return hashlib.md5(raw.encode()).hexdigest()


def fetch_reviews(count: int = 200, lang: str = "en", country: str = "np") -> list[dict]:
    """Fetch Play Store reviews and annotate with sentiment."""
    try:
        result, _ = reviews(
            ESEWA_PACKAGE,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=count,
        )
    except Exception as e:
        print(f"[PlayStore] Scrape error: {e}")
        return []

    parsed = []
    for r in result:
        text = r.get("content", "") or ""
        sa = analyze(text)
        parsed.append({
            "review_id": _make_id(r, "playstore"),
            "platform": "playstore",
            "user_name": r.get("userName", "Anonymous"),
            "rating": float(r.get("score", 0)),
            "text": text,
            "sentiment": sa["sentiment"],
            "sentiment_score": sa["score"],
            "app_version": r.get("appVersion", ""),
            "review_date": r.get("at", datetime.utcnow()),
            "thumbs_up": r.get("thumbsUpCount", 0),
        })
    return parsed
