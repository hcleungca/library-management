"""Semantic vector search Pydantic schemas.

Defines request and response schemas for vector similarity search,
including thresholding, filtering, and similarity score metrics.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.book import BookRead


class SemanticSearchRequest(BaseModel):
    """Request payload for conceptual vector search across catalog books."""

    query: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Search phrase, natural language query, or problem description",
    )
    limit: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of candidate books to return",
    )
    available_only: bool = Field(
        False,
        description="Filter results strictly to books currently on the stacks (AVAILABLE)",
    )
    genre: str | None = Field(
        None,
        max_length=100,
        description="Optional genre filter constraint",
    )
    min_similarity: float = Field(
        0.2,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity cutoff threshold (1.0 = exact match)",
    )


class SearchResultBook(BookRead):
    """Catalog book model enriched with vector similarity rankings."""

    model_config = ConfigDict(from_attributes=True)

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Computed cosine similarity score (1 - cosine_distance)",
    )
    cosine_distance: float = Field(
        ...,
        ge=0.0,
        description="Raw cosine distance from query embedding vector",
    )


class SemanticSearchResponse(BaseModel):
    """Response envelope containing ranked semantic search results."""

    query: str
    results: list[SearchResultBook]
    total_results: int

