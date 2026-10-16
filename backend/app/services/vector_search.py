"""pgvector Cosine Hybrid Search Service.

Executes semantic vector searches combining PostgreSQL pgvector cosine distance
with relational SQL filters (status, genre, decommissioned exclusions).
"""

import logging
import math
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.book import Book
from app.schemas.search import SearchResultBook
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)


def search_books_semantic(
    db: Session,
    query_text: str,
    limit: int = 10,
    available_only: bool = False,
    genre: str | None = None,
    min_similarity: float = 0.2,
) -> list[SearchResultBook]:
    """Execute hybrid semantic vector search against catalog books using pgvector.

    1. Embeds the natural language search query into a 1536-dim vector via FastEmbed.
    2. Builds single hybrid SQL query using pgvector cosine distance operator (<=>).
    3. Combines vector ranking with relational filters (status, genre, decommissioned).
    4. Calibrates similarity_score = round(1.0 - distance, 4) and applies cutoff threshold.
    """
    cleaned_query = (query_text or "").strip()
    if not cleaned_query:
        return []

    query_vector = generate_embedding(cleaned_query)

    # PostgreSQL pgvector native query using HNSW cosine distance operator <=>
    distance_expr = Book.embedding.cosine_distance(query_vector).label("distance")
    query = db.query(Book, distance_expr).filter(
        Book.embedding.is_not(None),
        Book.status != "DECOMMISSIONED",
    )

    if available_only:
        query = query.filter(Book.status == "AVAILABLE")

    if genre and genre.strip():
        query = query.filter(Book.genre.ilike(f"%{genre.strip()}%"))

    candidate_rows = query.order_by(distance_expr.asc()).limit(limit * 2).all()

    book_ids = [b.id for b, _ in candidate_rows]
    active_loan_book_ids: set[int] = set()
    if book_ids:
        from app.models.loan import Loan

        active_loans = (
            db.query(Loan.book_id)
            .filter(Loan.book_id.in_(book_ids), Loan.status == "ACTIVE")
            .all()
        )
        active_loan_book_ids = {row[0] for row in active_loans}

    results: list[SearchResultBook] = []
    for book, distance in candidate_rows:
        dist_val = float(distance) if distance is not None else 1.0
        similarity_score = round(1.0 - dist_val, 4)

        effective_status = "CHECKED_OUT" if book.id in active_loan_book_ids else book.status
        if available_only and effective_status != "AVAILABLE":
            continue

        if similarity_score >= min_similarity:
            results.append(
                SearchResultBook(
                    id=book.id,
                    title=book.title,
                    author=book.author,
                    isbn=book.isbn,
                    genre=book.genre,
                    publication_year=book.publication_year,
                    dewey_decimal=book.dewey_decimal,
                    summary=book.summary,
                    cover_image_url=book.cover_image_url,
                    status=effective_status,
                    created_at=book.created_at,
                    updated_at=book.updated_at,
                    similarity_score=similarity_score,
                    cosine_distance=round(dist_val, 4),
                )
            )
            if len(results) >= limit:
                break

    return results

    return results

