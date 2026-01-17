from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.schemas.event import EventIn
from app.schemas.feed import FeedItem, FeedResponse
from app.schemas.newsletter import NewsletterOut
from app.schemas.preferences import PreferencesIn, PreferencesOut
from app.schemas.topic import PopularTopicsResponse

__all__ = [
    "LoginRequest",
    "SignupRequest",
    "TokenResponse",
    "EventIn",
    "FeedItem",
    "FeedResponse",
    "NewsletterOut",
    "PreferencesIn",
    "PreferencesOut",
    "PopularTopicsResponse",
]
