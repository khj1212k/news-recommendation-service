from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://news:news_password@localhost:5432/news"
    secret_key: str = "change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    cors_origins: str = "http://localhost:3000"
    timezone: str = "Asia/Seoul"

    news_sources_file: str = "config/sources.yaml"
    news_request_timeout: float = 10.0
    news_user_agent: str = "NewsPipeline/1.0"
    news_max_items_per_source: int = 120

    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dim: int = 384

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1200
    mock_llm: bool = False

    topic_similarity_threshold: float = 0.88
    topic_merge_threshold: float = 0.94
    topic_time_window_days: int = 7
    dedup_near_threshold: float = 0.92
    newsletter_min_bullets: int = 5
    newsletter_max_bullets: int = 10

    max_feed_items: int = 30
    max_per_category: int = 6
    max_per_topic: int = 1
    ranker_model_path: str = "ml/artifacts/ranker.pkl"
    ranker_meta_path: str = "ml/artifacts/ranker_meta.json"
    mmr_lambda: float = 0.8
    mmr_max_candidates: int = 120
    user_embedding_decay_hours: int = 72

    class Config:
        env_prefix = ""


@lru_cache

def get_settings() -> Settings:
    return Settings()
