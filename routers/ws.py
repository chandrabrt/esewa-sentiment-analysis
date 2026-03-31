from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, Review
import asyncio
import json
from datetime import datetime


router = APIRouter(tags=["websocket"])

# Global connection manager
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


def _serialize(review: Review) -> dict:
    return {
        "id": review.id,
        "platform": review.platform,
        "user_name": review.user_name,
        "rating": review.rating,
        "text": review.text[:200],
        "sentiment": review.sentiment,
        "sentiment_score": review.sentiment_score,
        "review_date": review.review_date.isoformat() if review.review_date else None,
    }


@router.websocket("/ws/live-reviews")
async def live_reviews_ws(websocket: WebSocket):
    """
    WebSocket endpoint that polls for the 10 newest reviews every 15 seconds
    and broadcasts them to all connected clients.
    """
    await manager.connect(websocket)
    last_id = 0
    try:
        while True:
            db = SessionLocal()
            try:
                items = (
                    db.query(Review)
                    .filter(Review.id > last_id)
                    .order_by(Review.id.desc())
                    .limit(10)
                    .all()
                )
                if items:
                    last_id = items[0].id
                    for item in reversed(items):
                        await websocket.send_json({
                            "type": "new_review",
                            "data": _serialize(item),
                        })
            finally:
                db.close()
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_review(review_data: dict):
    """Call this after inserting a new review to push to all WS clients."""
    await manager.broadcast({"type": "new_review", "data": review_data})
