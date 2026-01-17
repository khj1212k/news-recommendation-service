from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, events, feed, newsletter, preferences, topics
from app.core.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(title="Korean News Recommendation Service", version="1.0.0")

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

app.include_router(auth.router)
app.include_router(feed.router)
app.include_router(topics.router)
app.include_router(newsletter.router)
app.include_router(events.router)
app.include_router(preferences.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
