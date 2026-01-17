from app.pipeline.pipeline_tasks import (
    assign_topics,
    clean_normalize,
    deduplicate,
    embed_newsletters,
    extract_keywords_task,
    fetch_articles,
    generate_newsletters,
    update_popularity,
)

__all__ = [
    "assign_topics",
    "clean_normalize",
    "deduplicate",
    "embed_newsletters",
    "extract_keywords_task",
    "fetch_articles",
    "generate_newsletters",
    "update_popularity",
]
