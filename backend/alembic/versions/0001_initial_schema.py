"""Initial schema with pgvector, profiles, books, loans, and maintenance_logs

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-14 21:00:00.000000

"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Profiles table
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.String(length=50),
            server_default="PATRON",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email"),
    )

    # 3. Books table
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("isbn", sa.String(length=32), nullable=True),
        sa.Column("genre", sa.String(length=100), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("dewey_decimal", sa.String(length=32), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="AVAILABLE",
            nullable=False,
        ),
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.Vector(1536),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)
    op.create_index(op.f("ix_books_author"), "books", ["author"], unique=False)
    op.create_index(op.f("ix_books_isbn"), "books", ["isbn"], unique=True)
    op.create_index(op.f("ix_books_genre"), "books", ["genre"], unique=False)
    op.create_index(op.f("ix_books_status"), "books", ["status"], unique=False)

    # HNSW Index for Cosine Distance Vector Search
    op.execute(
        "CREATE INDEX IF NOT EXISTS books_embedding_idx ON books "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # 4. Loans table
    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "borrowed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="ACTIVE",
            nullable=False,
        ),
    )
    # Concurrency control: Partial unique index guaranteeing at most 1 active loan per book
    op.create_index(
        "idx_unique_active_loan_per_book",
        "loans",
        ["book_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    # 5. Maintenance Logs table
    op.create_table(
        "maintenance_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "logged_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id"),
            nullable=False,
        ),
        sa.Column("damage_description", sa.Text(), nullable=False),
        sa.Column(
            "severity",
            sa.String(length=50),
            server_default="MODERATE",
            nullable=False,
        ),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    # Drop tables in reverse topological order
    op.drop_table("maintenance_logs")

    op.drop_index("idx_unique_active_loan_per_book", table_name="loans")
    op.drop_table("loans")

    op.execute("DROP INDEX IF EXISTS books_embedding_idx")
    op.drop_index(op.f("ix_books_status"), table_name="books")
    op.drop_index(op.f("ix_books_genre"), table_name="books")
    op.drop_index(op.f("ix_books_isbn"), table_name="books")
    op.drop_index(op.f("ix_books_author"), table_name="books")
    op.drop_index(op.f("ix_books_title"), table_name="books")
    op.drop_table("books")

    op.drop_table("profiles")

    op.execute("DROP EXTENSION IF EXISTS vector")
