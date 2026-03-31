from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio

from database import create_tables
from routers import reviews, stats, ws as ws_router
from seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed_if_empty()
    yield


app = FastAPI(
    title="eSewa Sentiment Analysis",
    description="Sentiment analysis dashboard for eSewa mobile app reviews",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(reviews.router)
app.include_router(stats.router)
app.include_router(ws_router.router)


# ─── Page routes ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "active": "dashboard"})


@app.get("/playstore", response_class=HTMLResponse)
async def playstore_page(request: Request):
    return templates.TemplateResponse("playstore.html", {"request": request, "active": "playstore"})


@app.get("/appstore", response_class=HTMLResponse)
async def appstore_page(request: Request):
    return templates.TemplateResponse("appstore.html", {"request": request, "active": "appstore"})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request, "active": "settings"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
