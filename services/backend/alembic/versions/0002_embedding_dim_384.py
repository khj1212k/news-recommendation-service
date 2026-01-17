"""Update embedding dimensions to 384.

Revision ID: 0002_embedding_dim_384
Revises: 0001_init
Create Date: 2026-01-17
"""

from alembic import op


revision = "0002_embedding_dim_384"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_newsletter_embeddings_embedding")
    op.execute("UPDATE topics SET centroid_embedding = NULL")
    op.execute("DELETE FROM newsletter_embeddings")
    op.execute("DELETE FROM user_embeddings")
    op.execute("ALTER TABLE topics ALTER COLUMN centroid_embedding TYPE vector(384)")
    op.execute("ALTER TABLE newsletter_embeddings ALTER COLUMN embedding TYPE vector(384)")
    op.execute("ALTER TABLE user_embeddings ALTER COLUMN embedding TYPE vector(384)")
    op.execute("UPDATE newsletter_embeddings SET dim = 384")
    op.execute("UPDATE user_embeddings SET dim = 384")
    op.execute(
        "CREATE INDEX ix_newsletter_embeddings_embedding ON newsletter_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_newsletter_embeddings_embedding")
    op.execute("ALTER TABLE topics ALTER COLUMN centroid_embedding TYPE vector(256)")
    op.execute("ALTER TABLE newsletter_embeddings ALTER COLUMN embedding TYPE vector(256)")
    op.execute("ALTER TABLE user_embeddings ALTER COLUMN embedding TYPE vector(256)")
    op.execute("UPDATE newsletter_embeddings SET dim = 256")
    op.execute("UPDATE user_embeddings SET dim = 256")
    op.execute(
        "CREATE INDEX ix_newsletter_embeddings_embedding ON newsletter_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )
