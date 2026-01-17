import json
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from app.core.config import get_settings
from app.utils.logger import get_logger
from app.utils.text_utils import split_sentences

logger = get_logger(__name__)


@dataclass
class NewsletterResult:
    text: str
    citations: List[Dict]


def _select_sentences(articles: List[Dict], max_per_article: int = 5) -> List[Tuple[str, Dict]]:
    selections: List[Tuple[str, Dict]] = []
    for article in articles:
        sentences = split_sentences(article.get("clean_text", ""))
        for sentence in sentences[:max_per_article]:
            if len(sentence) < 15:
                continue
            selections.append((sentence, article))
    return selections


def _build_evidence(articles: List[Dict], max_per_article: int = 5) -> List[Dict[str, Any]]:
    evidence = []
    for article in articles:
        sentences = split_sentences(article.get("clean_text", ""))
        trimmed = [s[:300] for s in sentences if s.strip()]
        selected = [s for s in trimmed[:max_per_article] if len(s) >= 15]
        if not selected:
            continue
        evidence.append(
            {
                "id": str(article.get("id")),
                "title": article.get("title", ""),
                "published_at": article.get("published_at"),
                "sentences": selected,
            }
        )
    return evidence


def _mock_generate_newsletter(topic_title: str, articles: List[Dict]) -> NewsletterResult:
    settings = get_settings()
    min_bullets = settings.newsletter_min_bullets
    max_bullets = settings.newsletter_max_bullets

    selections = _select_sentences(articles)
    if not selections:
        headline = "관련 기사 요약"
        body = "핵심 사실을 추출할 수 없습니다."
        text = f"[헤드라인] {headline}\n\n[핵심 사실]\n- {body}\n\n[확인된 내용]\n- {body}\n\n[불확실/논쟁 중]\n- {body}\n\n[배경]\n{body}"
        return NewsletterResult(text=text, citations=[])

    headline = topic_title or selections[0][1].get("title", "주요 이슈")

    bullets = selections[:max_bullets]
    if len(bullets) < min_bullets:
        bullets = bullets + selections[: (min_bullets - len(bullets))]

    confirmed = []
    disputed = []
    for sentence, article in bullets:
        if any(token in sentence for token in ["검토", "논의", "가능", "추가", "일부"]):
            disputed.append((sentence, article))
        else:
            confirmed.append((sentence, article))

    if not confirmed:
        confirmed = bullets[:max(1, min_bullets // 2)]
    if not disputed:
        disputed = bullets[-max(1, min_bullets // 3) :]

    context_sentence, context_article = selections[0]

    lines = [
        f"[헤드라인] {headline}",
        "",
        "[핵심 사실]",
    ]
    for sentence, _ in bullets:
        lines.append(f"- {sentence}")
    lines.append("")
    lines.append("[확인된 내용]")
    for sentence, _ in confirmed:
        lines.append(f"- {sentence}")
    lines.append("")
    lines.append("[불확실/논쟁 중]")
    for sentence, _ in disputed:
        lines.append(f"- {sentence}")
    lines.append("")
    lines.append("[배경]")
    lines.append(context_sentence)

    text = "\n".join(lines)

    citations: List[Dict] = []
    sentence_index = 0
    for sentence, article in bullets:
        citations.append(
            {
                "sentence_index": sentence_index,
                "source_article_id": str(article["id"]),
                "source_excerpt": sentence,
                "source_offset_start": None,
                "source_offset_end": None,
            }
        )
        sentence_index += 1
    for sentence, article in confirmed:
        citations.append(
            {
                "sentence_index": sentence_index,
                "source_article_id": str(article["id"]),
                "source_excerpt": sentence,
                "source_offset_start": None,
                "source_offset_end": None,
            }
        )
        sentence_index += 1
    for sentence, article in disputed:
        citations.append(
            {
                "sentence_index": sentence_index,
                "source_article_id": str(article["id"]),
                "source_excerpt": sentence,
                "source_offset_start": None,
                "source_offset_end": None,
            }
        )
        sentence_index += 1

    citations.append(
        {
            "sentence_index": sentence_index,
            "source_article_id": str(context_article["id"]),
            "source_excerpt": context_sentence,
            "source_offset_start": None,
            "source_offset_end": None,
        }
    )

    return NewsletterResult(text=text, citations=citations)


def _call_openai(system_prompt: str, user_payload: Dict[str, Any]) -> str:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI()
    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    )
    return response.choices[0].message.content or "{}"


def _call_anthropic(system_prompt: str, user_payload: Dict[str, Any]) -> str:
    from anthropic import Anthropic

    settings = get_settings()
    client = Anthropic()
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}],
    )
    return response.content[0].text if response.content else "{}"


def _build_newsletter_from_llm(payload: Dict[str, Any]) -> Tuple[str, List[Dict], int]:
    headline = payload.get("headline", "")
    bullets = payload.get("bullets", [])
    confirmed = payload.get("confirmed", [])
    disputed = payload.get("disputed", [])
    context = payload.get("context", {})

    lines = [
        f"[헤드라인] {headline}",
        "",
        "[핵심 사실]",
    ]
    sentence_index = 0
    citations: List[Dict] = []

    def add_items(items: List[Dict[str, Any]]) -> None:
        nonlocal sentence_index
        for item in items:
            text = item.get("text", "").strip()
            if not text:
                continue
            lines.append(f"- {text}")
            for citation in item.get("citations", []) or []:
                source_id = citation.get("article_id")
                excerpt = citation.get("excerpt")
                if not source_id or not excerpt:
                    continue
                citations.append(
                    {
                        "sentence_index": sentence_index,
                        "source_article_id": source_id,
                        "source_excerpt": excerpt,
                        "source_offset_start": None,
                        "source_offset_end": None,
                    }
                )
            sentence_index += 1

    add_items(bullets)
    lines.append("")
    lines.append("[확인된 내용]")
    add_items(confirmed)
    lines.append("")
    lines.append("[불확실/논쟁 중]")
    add_items(disputed)
    lines.append("")
    lines.append("[배경]")
    context_text = context.get("text", "").strip()
    if context_text:
        lines.append(context_text)
        for citation in context.get("citations", []) or []:
            source_id = citation.get("article_id")
            excerpt = citation.get("excerpt")
            if not source_id or not excerpt:
                continue
            citations.append(
                {
                    "sentence_index": sentence_index,
                    "source_article_id": source_id,
                    "source_excerpt": excerpt,
                    "source_offset_start": None,
                    "source_offset_end": None,
                }
            )
        sentence_index += 1

    return "\n".join(lines), citations, sentence_index


def generate_newsletter(topic_title: str, articles: List[Dict]) -> NewsletterResult:
    settings = get_settings()
    if settings.mock_llm or settings.llm_provider == "mock":
        return _mock_generate_newsletter(topic_title, articles)

    evidence = _build_evidence(articles)
    if not evidence:
        return _mock_generate_newsletter(topic_title, articles)

    system_prompt = (
        "너는 한국 뉴스레터 에디터다. 주어진 근거 문장만 사용해 요약하라. "
        "사실은 반드시 근거 문장에 의해 지지되어야 하며, 각 문장마다 인용을 제공하라. "
        "출력은 JSON 객체로만 반환한다."
    )
    user_payload = {
        "topic_title": topic_title,
        "requirements": {
            "bullet_count": {
                "min": settings.newsletter_min_bullets,
                "max": settings.newsletter_max_bullets,
            },
            "sections": ["bullets", "confirmed", "disputed", "context"],
            "citation_rule": "모든 문장에 citations 배열 포함. excerpt는 제공된 근거 문장과 완전히 동일해야 함.",
        },
        "evidence": evidence,
        "output_schema": {
            "headline": "string",
            "bullets": [{"text": "string", "citations": [{"article_id": "uuid", "excerpt": "string"}]}],
            "confirmed": [{"text": "string", "citations": [{"article_id": "uuid", "excerpt": "string"}]}],
            "disputed": [{"text": "string", "citations": [{"article_id": "uuid", "excerpt": "string"}]}],
            "context": {"text": "string", "citations": [{"article_id": "uuid", "excerpt": "string"}]},
        },
    }

    try:
        if settings.llm_provider == "openai":
            content = _call_openai(system_prompt, user_payload)
        elif settings.llm_provider == "anthropic":
            content = _call_anthropic(system_prompt, user_payload)
        else:
            raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")
        payload = json.loads(content)
        text, citations, sentence_count = _build_newsletter_from_llm(payload)
        if not text or not citations:
            raise ValueError("empty llm response")
        coverage = {idx for idx in range(sentence_count)}
        cited = {c["sentence_index"] for c in citations}
        if not coverage.issubset(cited):
            raise ValueError("empty llm response")
        return NewsletterResult(text=text, citations=citations)
    except Exception as exc:
        logger.warning("llm failed, falling back", extra={"extra": {"error": str(exc)}})
        return _mock_generate_newsletter(topic_title, articles)
