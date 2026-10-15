import importlib.util
from pathlib import Path


def test_initial_migration_file_exists():
    """Verify 0001_initial_schema.py migration script exists."""
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0001_initial_schema.py"
    )
    assert migration_path.exists()


def test_initial_migration_metadata_and_structure():
    """Verify revision ID, down_revision, and upgrade/downgrade functions."""
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0001_initial_schema.py"
    )

    spec = importlib.util.spec_from_file_location("initial_migration", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "0001_initial_schema"
    assert module.down_revision is None
    assert callable(module.upgrade)
    assert callable(module.downgrade)


def test_initial_migration_drops_deprecated_fields():
    """Verify total_copies and avatar_url are omitted from migration DDL."""
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0001_initial_schema.py"
    )
    content = migration_path.read_text()
    assert "total_copies" not in content
    assert "avatar_url" not in content
    assert "idx_unique_active_loan_per_book" in content
    assert "books_embedding_idx" in content

