"""Unit tests for semantic vector search Pydantic schemas."""

from datetime import UTC, datetime
import pytest
from pydantic import ValidationError

from app.schemas.book import BookStatus
from app.schemas.search import (
    SearchResultBook,
    SemanticSearchRequest,
    SemanticSearchResponse,
)


def test_semantic_search_request_valid_defaults():
    """Verify default values for SemanticSearchRequest."""
    req = SemanticSearchRequest(query="database internals")
    assert req.query == "database internals"
    assert req.limit == 10
    assert req.available_only is False
    assert req.genre is None
    assert req.min_similarity == 0.2


def test_semantic_search_request_custom_values():
    """Verify custom parameter initialization."""
    req = SemanticSearchRequest(
        query="distributed consensus raft paxos",
        limit=25,
        available_only=True,
        genre="Distributed Systems",
        min_similarity=0.75,
    )
    assert req.limit == 25
    assert req.available_only is True
    assert req.genre == "Distributed Systems"
    assert req.min_similarity == 0.75


def test_semantic_search_request_validation_errors():
    """Verify validation boundaries for query length, limit, and similarity thresholds."""
    # Query too short (<2 chars)
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="a")

    # Empty query
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="")

    # Limit below 1
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="test query", limit=0)

    # Limit above 50
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="test query", limit=51)

    # Similarity below 0.0
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="test query", min_similarity=-0.1)

    # Similarity above 1.0
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="test query", min_similarity=1.1)


def test_search_result_book_inheritance():
    """Verify SearchResultBook contains full BookRead attributes plus ranking scores."""
    now = datetime.now(UTC)
    result_book = SearchResultBook(
        id=1,
        title="Designing Data-Intensive Applications",
        author="Martin Kleppmann",
        isbn="978-1449373320",
        genre="Distributed Systems",
        publication_year=2017,
        dewey_decimal="005.74",
        summary="A comprehensive guide to distributed storage engines.",
        status=BookStatus.AVAILABLE,
        created_at=now,
        updated_at=now,
        similarity_score=0.92,
        cosine_distance=0.08,
    )
    assert result_book.id == 1
    assert result_book.title == "Designing Data-Intensive Applications"
    assert result_book.similarity_score == 0.92
    assert result_book.cosine_distance == 0.08
    assert result_book.status == BookStatus.AVAILABLE


def test_semantic_search_response_envelope():
    """Verify SemanticSearchResponse schema and serialized output."""
    now = datetime.now(UTC)
    book = SearchResultBook(
        id=42,
        title="Site Reliability Engineering",
        author="Betsy Beyer",
        isbn="978-1491929124",
        genre="DevOps & Reliability",
        status=BookStatus.AVAILABLE,
        created_at=now,
        updated_at=now,
        similarity_score=0.88,
        cosine_distance=0.12,
    )
    response = SemanticSearchResponse(
        query="SRE SLO error budget",
        results=[book],
        total_results=1,
    )
    assert response.query == "SRE SLO error budget"
    assert response.total_results == 1
    assert len(response.results) == 1
    assert response.results[0].title == "Site Reliability Engineering"

