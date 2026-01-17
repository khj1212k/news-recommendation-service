from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass
class ArticlePayload:
    source_name: str
    url: str
    title: str
    author: Optional[str]
    published_at: Optional[str]
    raw_text: str
    metadata: Dict


class BaseAdapter(ABC):
    @abstractmethod
    def fetch(self) -> Iterable[ArticlePayload]:
        raise NotImplementedError
