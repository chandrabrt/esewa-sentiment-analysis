import requests as req_lib
from datetime import datetime
from sentiment.analyzer import analyze
import hashlib


ESEWA_APP_ID = "969682311"


def _make_id(r: dict) -> str:
    raw = f"appstore-{r.get('id', r.get('name', ''))}"
    return hashlib.md5(raw.encode()).hexdigest()


def fetch_reviews(count: int = 200, country: str = "np") -> list[dict]:
    """
    Fetch App Store reviews using iTunes RSS feed (no third-party library).
    Apple provides up to 500 reviews (10 pages × 50 reviews each).
    """
    reviews = []
    pages = min(10, max(1, (count + 49) // 50))

    for page in range(1, pages + 1):
        url = (
            f"https://itunes.apple.com/{country}/rss/customerreviews/"
            f"page={page}/id={ESEWA_APP_ID}/sortby=mostrecent/json"
        )
        try:
            resp = req_lib.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            feed = data.get("feed", {})
            entries = feed.get("entry", [])

            if not entries:
                break

            for e in entries:
                # Skip the app itself (first entry is app metadata)
                if not e.get("im:rating"):
                    continue

                title = e.get("title", {}).get("label", "")
                body = e.get("content", {}).get("label", "")
                full_text = f"{title}. {body}".strip(". ") if title else body

                try:
                    rating = float(e["im:rating"]["label"])
                except (KeyError, ValueError):
                    rating = 0.0

                version = e.get("im:version", {}).get("label", "")
                author = e.get("author", {}).get("name", {}).get("label", "Anonymous")
                entry_id = e.get("id", {}).get("label", "")

                sa = analyze(full_text)
                reviews.append({
                    "review_id": hashlib.md5(f"appstore-{entry_id}".encode()).hexdigest(),
                    "platform": "appstore",
                    "user_name": author,
                    "rating": rating,
                    "text": full_text,
                    "sentiment": sa["sentiment"],
                    "sentiment_score": sa["score"],
                    "app_version": version,
                    "review_date": datetime.utcnow(),
                    "thumbs_up": 0,
                })

                if len(reviews) >= count:
                    return reviews
        except Exception as e:
            print(f"[AppStore] Page {page} failed: {e}")
            break

    return reviews
