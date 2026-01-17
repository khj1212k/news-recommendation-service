from typing import List, Optional

from pydantic import BaseModel


class FeedItem(BaseModel):
    newsletter_id: str
    topic_id: str
    title: Optional[str]
    category: Optional[str]
    newsletter_text: str
    created_at: str
    popularity_count: int
    reason: str


class FeedResponse(BaseModel):
    items: List[FeedItem]
