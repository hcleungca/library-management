"""Unit tests for the pgvector hybrid cosine search service."""

from unittest.mock import MagicMock, patch
from datetime import UTC, datetime
from app.models.book import Book
from app.services.vector_search import search_books_semantic


def test_search_books_semantic_empty_query():
    """Verify empty query returns empty list without querying DB."""
    mock_db = MagicMock()
    results = search_books_semantic(db=mock_db, query_text="   ")
    assert results == []
    mock_db.query.assert_not_called()


@patch("app.services.vector_search.generate_embedding")
def test_search_books_semantic_execution_and_threshold(mock_generate_embedding):
    """Verify search queries DB with cosine distance and filters by min_similarity."""
    mock_generate_embedding.return_value = [0.1] * 1536

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query

    # Create dummy books
    book1 = MagicMock(spec=Book)
    book1.id = 1
    book1.title = "Designing Data-Intensive Applications"
    book1.author = "Martin Kleppmann"
    book1.isbn = "9781449373320"
    book1.genre = "Distributed Systems"
    book1.publication_year = 2017
    book1.dewey_decimal = "005.74"
    book1.summary = "A comprehensive guide to reliable systems."
    book1.cover_image_url = None
    book1.status = "AVAILABLE"
    book1.created_at = datetime.now(UTC)
    book1.updated_at = datetime.now(UTC)

    # book1 has distance 0.15 => similarity 0.85
    # book2 has distance 0.90 => similarity 0.10 (should be filtered out by min_similarity=0.2)
    book2 = MagicMock(spec=Book)
    book2.id = 2
    book2.title = "Unrelated Book"
    book2.author = "Anonymous"
    book2.isbn = "9780000000000"
    book2.genre = "Fiction"
    book2.publication_year = 2020
    book2.dewey_decimal = "800.00"
    book2.summary = "A story."
    book2.cover_image_url = None
    book2.status = "AVAILABLE"
    book2.created_at = datetime.now(UTC)
    book2.updated_at = datetime.now(UTC)

    mock_query.limit.return_value.all.return_value = [
        (book1, 0.15),
        (book2, 0.90),
    ]

    results = search_books_semantic(
        db=mock_db,
        query_text="database scaling",
        limit=5,
        min_similarity=0.2,
    )

    assert len(results) == 1
    assert results[0].id == 1
    assert results[0].title == "Designing Data-Intensive Applications"
    assert results[0].similarity_score == 0.85
    assert results[0].cosine_distance == 0.15
