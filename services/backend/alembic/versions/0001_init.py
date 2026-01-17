"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2024-01-17 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE newsletterstatus AS ENUM ('ok', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE eventtype AS ENUM ('impression', 'click', 'dwell', 'hide', 'follow', 'save');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )
    newsletterstatus = postgresql.ENUM(
        "ok",
        "failed",
        name="newsletterstatus",
        create_type=False,
        _create_events=False,
    )
    eventtype = postgresql.ENUM(
        "impression",
        "click",
        "dwell",
        "hide",
        "follow",
        "save",
        name="eventtype",
        create_type=False,
        _create_events=False,
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("base_url", sa.String(), nullable=True),
        sa.Column("terms_url", sa.String(), nullable=True),
        sa.Column("allow_fulltext", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allow_derivatives", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("url", sa.String(), nullable=False, unique=True),
        sa.Column("url_canonical", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("clean_text", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_url_canonical", "articles", ["url_canonical"])
    op.create_index("ix_articles_content_hash", "articles", ["content_hash"])

    op.create_table(
        "article_keywords",
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id"), primary_key=True),
        sa.Column("keyword", sa.String(), primary_key=True),
        sa.Column("method", sa.String(), primary_key=True),
        sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_article_keywords_keyword", "article_keywords", ["keyword"])

    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("popularity_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("centroid_embedding", Vector(384), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_topics_last_updated_at", "topics", ["last_updated_at"])
    op.create_index("ix_topics_category", "topics", ["category"])

    op.create_table(
        "topic_articles",
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), primary_key=True),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
    )

    op.create_table(
        "newsletters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column("newsletter_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("llm_model", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("status", newsletterstatus, nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("topic_id", "content_hash", name="uq_newsletter_topic_hash"),
    )
    op.create_index("ix_newsletters_topic_id", "newsletters", ["topic_id"])
    op.create_index("ix_newsletters_created_at", "newsletters", ["created_at"])
    op.create_index("ix_newsletters_content_hash", "newsletters", ["content_hash"])

    op.create_table(
        "newsletter_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("newsletter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("newsletters.id"), nullable=False),
        sa.Column("sentence_index", sa.Integer(), nullable=False),
        sa.Column("source_article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        sa.Column("source_offset_start", sa.Integer(), nullable=True),
        sa.Column("source_offset_end", sa.Integer(), nullable=True),
    )

    op.create_table(
        "newsletter_embeddings",
        sa.Column("newsletter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("newsletters.id"), primary_key=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("dim", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
    )
    op.create_index(
        "ix_newsletter_embeddings_embedding",
        "newsletter_embeddings",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 50},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("categories", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "user_embeddings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("dim", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", eventtype, nullable=False),
        sa.Column("newsletter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("newsletters.id"), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("value", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("user_embeddings")
    op.drop_table("user_preferences")
    op.drop_table("users")
    op.drop_index("ix_newsletter_embeddings_embedding", table_name="newsletter_embeddings")
    op.drop_table("newsletter_embeddings")
    op.drop_table("newsletter_citations")
    op.drop_index("ix_newsletters_content_hash", table_name="newsletters")
    op.drop_index("ix_newsletters_created_at", table_name="newsletters")
    op.drop_index("ix_newsletters_topic_id", table_name="newsletters")
    op.drop_table("newsletters")
    op.drop_table("topic_articles")
    op.drop_index("ix_topics_category", table_name="topics")
    op.drop_index("ix_topics_last_updated_at", table_name="topics")
    op.drop_table("topics")
    op.drop_index("ix_article_keywords_keyword", table_name="article_keywords")
    op.drop_table("article_keywords")
    op.drop_index("ix_articles_content_hash", table_name="articles")
    op.drop_index("ix_articles_url_canonical", table_name="articles")
    op.drop_index("ix_articles_published_at", table_name="articles")
    op.drop_table("articles")
    op.drop_table("sources")

    eventtype = sa.Enum("impression", "click", "dwell", "hide", "follow", "save", name="eventtype")
    newsletterstatus = sa.Enum("ok", "failed", name="newsletterstatus")
    eventtype.drop(op.get_bind(), checkfirst=True)
    newsletterstatus.drop(op.get_bind(), checkfirst=True)
