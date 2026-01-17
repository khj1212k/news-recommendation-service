from typing import List, Optional

from pydantic import BaseModel


class PopularTopicOut(BaseModel):
    topic_id: str
    title: Optional[str]
    category: Optional[str]
    popularity_count: int
    newsletter_id: Optional[str]
    newsletter_text: Optional[str]
    created_at: Optional[str]


class PopularTopicsResponse(BaseModel):
    items: List[PopularTopicOut]
