from pathlib import Path


def test_schema_sql_file_exists():
    """Verify backend/scripts/schema.sql exists and is non-empty."""
    schema_path = Path(__file__).resolve().parents[1] / "scripts" / "schema.sql"
    assert schema_path.exists()
    content = schema_path.read_text()
    assert len(content) > 0


def test_schema_sql_core_ddl_components():
    """Verify required DDL statements, tables, extensions, and concurrency indexes exist."""
    schema_path = Path(__file__).resolve().parents[1] / "scripts" / "schema.sql"
    content = schema_path.read_text()

    # Extension & Types
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in content
    assert "book_status AS ENUM" in content
    assert "user_role AS ENUM" in content

    # Core Tables
    assert "CREATE TABLE IF NOT EXISTS profiles" in content
    assert "CREATE TABLE IF NOT EXISTS books" in content
    assert "CREATE TABLE IF NOT EXISTS loans" in content

    # Vector & Indexing
    assert "books_embedding_idx ON books USING hnsw (embedding vector_cosine_ops);" in content
    assert "idx_unique_active_loan_per_book ON loans (book_id) WHERE status = 'ACTIVE';" in content

    # Dropped fields are not present
    assert "total_copies" not in content
    assert "avatar_url" not in content

