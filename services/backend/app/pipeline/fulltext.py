from __future__ import annotations

from bs4 import BeautifulSoup
import trafilatura


def extract_fulltext(html: str) -> str:
    if not html:
        return ""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if text:
        return text.strip()
    soup = BeautifulSoup(html, "lxml")
    article = soup.find("article") or soup.find("main")
    if article:
        return article.get_text(" ", strip=True)
    return soup.get_text(" ", strip=True)
