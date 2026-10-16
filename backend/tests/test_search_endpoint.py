"""Unit tests for the semantic search REST endpoint (/api/books/search)."""

from datetime import UTC, datetime
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.search import SearchResultBook

client = TestClient(app)


def test_search_route_registered():
    """Verify /api/books/search route is registered in the FastAPI app with GET and POST."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/books/search" in openapi_paths
    assert "post" in openapi_paths["/api/books/search"]
    assert "get" in openapi_paths["/api/books/search"]


@patch("app.api.search.search_books_semantic")
def test_search_books_post_success(mock_search_semantic):
    """Verify POST /api/books/search returns 200 with SemanticSearchResponse schema."""
    dummy_book = SearchResultBook(
        id=1,
        title="Designing Data-Intensive Applications",
        author="Martin Kleppmann",
        isbn="9781449373320",
        genre="Distributed Systems",
        publication_year=2017,
        dewey_decimal="005.74",
        summary="Reliable, scalable, and maintainable systems.",
        cover_image_url=None,
        status="AVAILABLE",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        similarity_score=0.88,
        cosine_distance=0.12,
    )
    mock_search_semantic.return_value = [dummy_book]

    payload = {
        "query": "distributed storage and consensus",
        "limit": 5,
        "available_only": True,
        "genre": "Distributed Systems",
        "min_similarity": 0.5,
    }

    response = client.post("/api/books/search", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "distributed storage and consensus"
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == 1
    assert data["results"][0]["similarity_score"] == 0.88
    assert data["results"][0]["cosine_distance"] == 0.12

    # Verify search_books_semantic called with parsed parameters
    mock_search_semantic.assert_called_once()
    _, kwargs = mock_search_semantic.call_args
    assert kwargs["query_text"] == "distributed storage and consensus"
    assert kwargs["limit"] == 5
    assert kwargs["available_only"] is True
    assert kwargs["genre"] == "Distributed Systems"
    assert kwargs["min_similarity"] == 0.5


@patch("app.api.search.search_books_semantic")
def test_search_books_get_success(mock_search_semantic):
    """Verify GET /api/books/search returns 200 with SemanticSearchResponse schema."""
    dummy_book = SearchResultBook(
        id=2,
        title="Clean Architecture",
        author="Robert C. Martin",
        isbn="9780134494166",
        genre="Software Engineering",
        publication_year=2017,
        dewey_decimal="005.1",
        summary="A craftsman's guide to software structure and design.",
        cover_image_url=None,
        status="AVAILABLE",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        similarity_score=0.91,
        cosine_distance=0.09,
    )
    mock_search_semantic.return_value = [dummy_book]

    response = client.get("/api/books/search?q=clean+code+principles&limit=3&available_only=true")
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "clean code principles"
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == 2
    assert data["results"][0]["title"] == "Clean Architecture"

    mock_search_semantic.assert_called_once()
    _, kwargs = mock_search_semantic.call_args
    assert kwargs["query_text"] == "clean code principles"
    assert kwargs["limit"] == 3
    assert kwargs["available_only"] is True


def test_search_books_validation_errors():
    """Verify 422 Unprocessable Entity on invalid input."""
    # POST with query string shorter than 2 chars
    resp1 = client.post("/api/books/search", json={"query": "a"})
    assert resp1.status_code == 422

    # POST with empty body
    resp2 = client.post("/api/books/search", json={})
    assert resp2.status_code == 422

    # GET without required query parameter 'q'
    resp3 = client.get("/api/books/search")
    assert resp3.status_code == 422

