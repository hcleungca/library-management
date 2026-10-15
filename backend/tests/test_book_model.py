from app.models.book import Book


def test_book_table_name():
    """Verify table name is books."""
    assert Book.__tablename__ == "books"


def test_book_columns():
    """Verify Book columns exist and match specification."""
    columns = {c.name for c in Book.__table__.columns}
    expected = {
        "id",
        "title",
        "author",
        "isbn",
        "genre",
        "publication_year",
        "dewey_decimal",
        "summary",
        "cover_image_url",
        "status",
        "embedding",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)
    # Explicitly verify total_copies was dropped per architecture decision
    assert "total_copies" not in columns


def test_book_column_constraints():
    """Verify constraints: id is PK, indexes, default status, and vector dim."""
    table = Book.__table__

    assert table.columns["id"].primary_key is True
    assert table.columns["title"].nullable is False
    assert table.columns["title"].index is True

    assert table.columns["author"].nullable is False
    assert table.columns["author"].index is True

    assert table.columns["isbn"].unique is True
    assert table.columns["isbn"].index is True

    assert table.columns["status"].default.arg == "AVAILABLE"
    assert table.columns["status"].index is True

    # Vector dimension
    assert table.columns["embedding"].type.dim == 1536

