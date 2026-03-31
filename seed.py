"""
Seed the database with demo reviews if it is empty.
Called automatically on startup via FastAPI lifespan.
"""
from datetime import datetime, timedelta
import random
from database import SessionLocal, Review


DEMO_REVIEWS = [
    # Positive - Play Store
    {"user_name": "Rajan Sharma", "rating": 5, "text": "eSewa is the best digital wallet in Nepal! Fast transactions and great UI.", "platform": "playstore", "app_version": "5.12.0"},
    {"user_name": "Sunita Gurung", "rating": 5, "text": "Really fast and reliable. Never had any issues with money transfers.", "platform": "playstore", "app_version": "5.12.0"},
    {"user_name": "Bikram KC", "rating": 4, "text": "Excellent app. QR payment is very smooth. Minor UI improvements needed.", "platform": "playstore", "app_version": "5.11.2"},
    {"user_name": "Priya Acharya", "rating": 5, "text": "Best fintech app. Paying bills, recharging mobile, everything in one place.", "platform": "playstore", "app_version": "5.12.0"},
    {"user_name": "Amit Thapa", "rating": 4, "text": "Convenient and trustworthy. The cashback offers are fantastic!", "platform": "playstore", "app_version": "5.11.0"},
    {"user_name": "Nisha Tamang", "rating": 5, "text": "Love using eSewa. Transaction history is clear. 5 stars!", "platform": "playstore", "app_version": "5.12.1"},
    # Negative - Play Store
    {"user_name": "Dipesh Oli", "rating": 2, "text": "App crashes frequently. Often shows error during payment. Very frustrating!", "platform": "playstore", "app_version": "5.10.0"},
    {"user_name": "Hari Bhattarai", "rating": 1, "text": "Terrible update. The new version is extremely slow and lags a lot.", "platform": "playstore", "app_version": "5.12.0"},
    {"user_name": "Samir Yadav", "rating": 2, "text": "Customer support is very poor. Money got stuck and no response for days.", "platform": "playstore", "app_version": "5.11.0"},
    # Neutral - Play Store
    {"user_name": "Binita Khadka", "rating": 3, "text": "Works fine most of the time but could use a better dark mode.", "platform": "playstore", "app_version": "5.10.2"},
    {"user_name": "Roshan Poudel", "rating": 3, "text": "Decent app, does what it promises. Interface could be more modern.", "platform": "playstore", "app_version": "5.11.2"},
    # Positive - App Store
    {"user_name": "Anita Maharjan", "rating": 5, "text": "Great app! iOS version is very polished and fast.", "platform": "appstore", "app_version": "5.12.0"},
    {"user_name": "Sagar Rai", "rating": 5, "text": "eSewa has transformed how I pay. Sending money is instant and easy.", "platform": "appstore", "app_version": "5.12.0"},
    {"user_name": "Kabita Shrestha", "rating": 4, "text": "Smooth and intuitive. Biometric login is a great feature.", "platform": "appstore", "app_version": "5.11.1"},
    {"user_name": "Nabin Limbu", "rating": 5, "text": "Outstanding digital wallet. Best in Nepal by far. Highly recommend!", "platform": "appstore", "app_version": "5.12.0"},
    {"user_name": "Deepa Pandit", "rating": 4, "text": "Very convenient and reliable. The promotions on festivals are amazing.", "platform": "appstore", "app_version": "5.12.0"},
    # Negative - App Store
    {"user_name": "Pramod Joshi", "rating": 1, "text": "App keeps crashing after the latest iOS update. Cannot make payments!", "platform": "appstore", "app_version": "5.11.0"},
    {"user_name": "Manisha Dhakal", "rating": 2, "text": "Face ID login stopped working. Very inconvenient. Please fix soon.", "platform": "appstore", "app_version": "5.12.0"},
    # Neutral - App Store
    {"user_name": "Tilak Bista", "rating": 3, "text": "Okay app. Transaction fees could be lower for frequent users.", "platform": "appstore", "app_version": "5.11.2"},
    {"user_name": "Rekha Adhikari", "rating": 3, "text": "Works as expected but the statement export feature needs work.", "platform": "appstore", "app_version": "5.12.0"},
]


def seed_if_empty():
    db = SessionLocal()
    try:
        count = db.query(Review).count()
        if count > 0:
            return  # Already has data

        from sentiment.analyzer import analyze
        import hashlib

        base_date = datetime.utcnow() - timedelta(days=180)
        for i, r in enumerate(DEMO_REVIEWS):
            sa = analyze(r["text"])
            days_offset = random.randint(0, 180)
            review_date = base_date + timedelta(days=days_offset)
            rid = hashlib.md5(f"seed-{i}-{r['user_name']}".encode()).hexdigest()
            review = Review(
                review_id=rid,
                platform=r["platform"],
                user_name=r["user_name"],
                rating=float(r["rating"]),
                text=r["text"],
                sentiment=sa["sentiment"],
                sentiment_score=sa["score"],
                app_version=r.get("app_version", ""),
                review_date=review_date,
                thumbs_up=random.randint(0, 50),
            )
            db.add(review)
        db.commit()
        print(f"[Seed] Inserted {len(DEMO_REVIEWS)} demo reviews.")
    finally:
        db.close()
