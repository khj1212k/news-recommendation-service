from app.pipeline.adapters.base import ArticlePayload, BaseAdapter
from app.pipeline.adapters.rss import RssAdapter
from app.pipeline.adapters.newspaper import NewspaperAdapter

__all__ = ["ArticlePayload", "BaseAdapter", "RssAdapter", "NewspaperAdapter"]

