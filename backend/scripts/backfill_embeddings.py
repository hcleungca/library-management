"""Backfill vector embeddings for all catalog books.

Finds any catalog books in PostgreSQL with missing (NULL) embeddings,
computes 1536-dimensional FastEmbed normalized vectors, and saves them
so they become immediately discoverable via semantic vector search.
"""

import sys
import logging
from sqlalchemy import or_

from app.db.session import SessionLocal
from app.models.book import Book
from app.services.embedding_service import generate_embedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def backfill_book_embeddings(force_all: bool = False) -> int:
    """Iterate over catalog books and generate missing embeddings."""
    db = SessionLocal()
    updated_count = 0

    try:
        query = db.query(Book)
        if not force_all:
            query = query.filter(Book.embedding.is_(None))

        books_to_update = query.all()
        total_found = len(books_to_update)
        logger.info(f"Found {total_found} book(s) needing vector embeddings.")

        if total_found == 0:
            logger.info("All books already have valid vector embeddings.")
            return 0

        for i, book in enumerate(books_to_update, 1):
            embed_text = f"{book.title} {book.author} {book.genre or ''} {book.summary or ''}".strip()
            if embed_text:
                book.embedding = generate_embedding(embed_text)
                updated_count += 1
                logger.info(f"[{i}/{total_found}] Generated embedding for: #{book.id} '{book.title}'")

        db.commit()
        logger.info(f"Successfully committed embeddings for {updated_count} book(s).")
        return updated_count

    except Exception as exc:
        db.rollback()
        logger.error(f"Error backfilling embeddings: {exc}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv
    count = backfill_book_embeddings(force_all=force)
    print(f"Backfill finished: {count} books updated.")

