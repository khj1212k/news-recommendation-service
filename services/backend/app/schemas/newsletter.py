from typing import List, Optional

from pydantic import BaseModel


class CitationOut(BaseModel):
    sentence_index: int
    source_article_id: str
    source_excerpt: str
    source_offset_start: Optional[int]
    source_offset_end: Optional[int]


class SourceOut(BaseModel):
    id: str
    url: str
    title: Optional[str]
    publisher: Optional[str]
    published_at: Optional[str]


class NewsletterOut(BaseModel):
    id: str
    topic_id: str
    category: Optional[str]
    title: Optional[str]
    newsletter_text: str
    created_at: str
    citations: List[CitationOut]
    sources: List[SourceOut]
