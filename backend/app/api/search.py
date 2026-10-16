"""Semantic vector search API router.

Exposes endpoints for natural language conceptual book searches across the catalog
powered by pgvector cosine similarity.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import SemanticSearchRequest, SemanticSearchResponse
from app.services.vector_search import search_books_semantic

router = APIRouter(prefix="/books/search", tags=["Search"])


@router.post("", response_model=SemanticSearchResponse)
def search_books_endpoint(
    req: SemanticSearchRequest,
    db: Session = Depends(get_db),
) -> SemanticSearchResponse:
    """Semantic vector search across catalog books via POST request payload."""
    results = search_books_semantic(
        db=db,
        query_text=req.query,
        limit=req.limit,
        available_only=req.available_only,
        genre=req.genre,
        min_similarity=req.min_similarity,
    )
    return SemanticSearchResponse(
        query=req.query,
        results=results,
        total_results=len(results),
    )


@router.get("", response_model=SemanticSearchResponse)
def search_books_get_endpoint(
    q: str = Query(..., min_length=1, max_length=500, description="Search query string"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of candidate books to return"),
    available_only: bool = Query(False, description="Filter results strictly to available books"),
    genre: str | None = Query(None, max_length=100, description="Optional genre filter"),
    min_similarity: float = Query(0.2, ge=0.0, le=1.0, description="Minimum cosine similarity cutoff"),
    db: Session = Depends(get_db),
) -> SemanticSearchResponse:
    """Convenience GET endpoint for semantic vector search via URL query parameters."""
    results = search_books_semantic(
        db=db,
        query_text=q,
        limit=limit,
        available_only=available_only,
        genre=genre,
        min_similarity=min_similarity,
    )
    return SemanticSearchResponse(
        query=q,
        results=results,
        total_results=len(results),
    )

