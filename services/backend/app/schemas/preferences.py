from typing import List, Optional

from pydantic import BaseModel, Field


class PreferencesIn(BaseModel):
    categories: Optional[List[str]] = Field(default=None)
    keywords: Optional[List[str]] = Field(default=None)


class PreferencesOut(BaseModel):
    categories: List[str]
    keywords: List[str]
