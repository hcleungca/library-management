"""AI Librarian PydanticAI tool definitions & execution dispatcher.

Exposes four core database-grounded tools for the autonomous AI Librarian:
1. search_catalog: Semantic vector search using FastEmbed + pgvector cosine similarity.
2. check_availability: Checks book status and attaches Human-in-the-Loop checkout card.
3. borrow_book: Concurrency-safe loan creation for the authenticated patron.
4. get_my_active_loans: Queries the authenticated patron's active loans and due dates.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from pydantic_ai import RunContext
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.loan import Loan
from app.schemas.agent import ToolExecutionRecord
from app.services.vector_search import search_books_semantic

logger = logging.getLogger(__name__)


@dataclass
class LibraryContext:
    """Dependency container injected into PydanticAI agent tools via RunContext."""

    db: Session
    user_id: UUID
    user_role: str = "PATRON"
    tools_executed: list[ToolExecutionRecord] = field(default_factory=list)
    interactive_card: dict[str, Any] | None = None


def search_catalog(
    ctx: RunContext[LibraryContext],
    query: str,
    genre: str | None = None,
) -> list[dict[str, Any]]:
    """Search the library catalog for books matching a natural language topic, concept, problem, or genre.

    Args:
        ctx: PydanticAI runtime context with database session and patron identity.
        query: The natural language search phrase or problem description.
        genre: Optional genre filter (e.g. 'Distributed Systems', 'Database Systems').

    Returns:
        A list of top matching books with id, title, author, genre, status, summary, and similarity score.
    """
    try:
        results = search_books_semantic(
            db=ctx.deps.db,
            query_text=query,
            limit=5,
            genre=genre,
            min_similarity=0.15,
        )

        formatted: list[dict[str, Any]] = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "genre": b.genre,
                "status": b.status,
                "summary": b.summary,
                "cover_image_url": b.cover_image_url,
                "similarity_score": b.similarity_score,
            }
            for b in results
        ]

        # If multiple books were found, attach BOOK_LIST card for patron carousel
        if len(formatted) > 1:
            ctx.deps.interactive_card = {
                "type": "BOOK_LIST",
                "books": formatted,
            }

        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="search_catalog",
                arguments={"query": query, "genre": genre},
                result=formatted,
            )
        )
        return formatted

    except Exception as exc:
        logger.error("Error executing search_catalog tool: %s", exc, exc_info=True)
        err_res = [{"error": f"Failed to search catalog: {exc}"}]
        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="search_catalog",
                arguments={"query": query, "genre": genre},
                result=err_res,
            )
        )
        return err_res


def check_availability(
    ctx: RunContext[LibraryContext],
    book_id: int,
) -> dict[str, Any]:
    """Check inventory status for a specific book by ID to verify if it is immediately available on the stacks.

    Args:
        ctx: PydanticAI runtime context with database session and patron identity.
        book_id: The unique integer ID of the catalog book.

    Returns:
        Dictionary indicating whether the book is found, its title, and availability status.
    """
    try:
        book = (
            ctx.deps.db.query(Book)
            .filter(Book.id == book_id, Book.status != "DECOMMISSIONED")
            .first()
        )

        if not book:
            res = {"found": False, "message": f"Book #{book_id} not found in catalog."}
        else:
            is_avail = (book.status == "AVAILABLE")
            res = {
                "found": True,
                "book_id": book.id,
                "title": book.title,
                "author": book.author,
                "status": book.status,
                "is_available": is_avail,
            }

            # Human-in-the-Loop Safeguard: attach confirmation card proposal only for patrons
            if is_avail and ctx.deps.user_role == "PATRON":
                ctx.deps.interactive_card = {
                    "type": "CONFIRM_BORROW",
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "cover_image_url": book.cover_image_url,
                    "due_days": 14,
                }

        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="check_availability",
                arguments={"book_id": book_id},
                result=res,
            )
        )
        return res

    except Exception as exc:
        logger.error("Error executing check_availability tool: %s", exc, exc_info=True)
        err_res = {"error": f"Failed to check availability: {exc}"}
        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="check_availability",
                arguments={"book_id": book_id},
                result=err_res,
            )
        )
        return err_res


def borrow_book(
    ctx: RunContext[LibraryContext],
    book_id: int,
) -> dict[str, Any]:
    """Check out an available book for the authenticated patron.

    CRITICAL SAFETY REQUIREMENT:
    Do NOT call this tool unless the patron has explicitly confirmed they want to borrow the book.

    Args:
        ctx: PydanticAI runtime context containing authenticated patron user_id and DB session.
        book_id: The unique integer ID of the book to check out.

    Returns:
        Checkout confirmation with loan ID, book title, and calculated return due date.
    """
    if ctx.deps.user_role != "PATRON":
        res = {
            "success": False,
            "error": "Only patrons may borrow books. Staff and librarians cannot check out books.",
        }
        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="borrow_book",
                arguments={"book_id": book_id},
                result=res,
            )
        )
        return res

    db = ctx.deps.db
    user_id = ctx.deps.user_id

    try:
        # Acquire row-level lock on the book to prevent concurrent checkout races
        book = (
            db.query(Book)
            .filter(Book.id == book_id, Book.status != "DECOMMISSIONED")
            .with_for_update()
            .first()
        )

        if not book:
            res = {"success": False, "error": f"Book #{book_id} not found."}
        elif book.status != "AVAILABLE":
            res = {
                "success": False,
                "error": f"Book '{book.title}' is currently {book.status} and cannot be checked out.",
            }
        else:
            # Check for existing active loan on the same book
            active_loan = (
                db.query(Loan)
                .filter(Loan.book_id == book_id, Loan.status == "ACTIVE")
                .first()
            )
            if active_loan:
                res = {
                    "success": False,
                    "error": f"Book '{book.title}' already has an active loan.",
                }
            else:
                now = datetime.now(UTC)
                due_date = now + timedelta(days=14)

                loan = Loan(
                    book_id=book.id,
                    user_id=user_id,
                    borrowed_at=now,
                    due_date=due_date,
                    status="ACTIVE",
                )
                book.status = "CHECKED_OUT"
                book.updated_at = now

                db.add(loan)
                db.commit()
                db.refresh(loan)

                due_date_str = due_date.strftime("%Y-%m-%d")
                card = {
                    "type": "LOAN_RECEIPT",
                    "loan_id": loan.id,
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "cover_image_url": book.cover_image_url,
                    "due_date": due_date_str,
                }
                ctx.deps.interactive_card = card

                res = {
                    "success": True,
                    "loan_id": loan.id,
                    "book_id": book.id,
                    "title": book.title,
                    "due_date": due_date_str,
                    "message": f"Successfully checked out '{book.title}'! Due date: {due_date_str}.",
                }

        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="borrow_book",
                arguments={"book_id": book_id},
                result=res,
            )
        )
        return res

    except Exception as exc:
        db.rollback()
        logger.error("Error executing borrow_book tool: %s", exc, exc_info=True)
        err_res = {"success": False, "error": f"Checkout failed: {exc}"}
        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="borrow_book",
                arguments={"book_id": book_id},
                result=err_res,
            )
        )
        return err_res


def get_my_active_loans(
    ctx: RunContext[LibraryContext],
) -> list[dict[str, Any]]:
    """Retrieve all books currently checked out by the authenticated patron with due dates and overdue statuses.

    Args:
        ctx: PydanticAI runtime context containing authenticated patron user_id and DB session.

    Returns:
        List of the patron's active loans with book title, author, borrow date, and due date.
    """
    db = ctx.deps.db
    user_id = ctx.deps.user_id

    try:
        active_loans = (
            db.query(Loan)
            .filter(Loan.user_id == user_id, Loan.status == "ACTIVE")
            .order_by(Loan.due_date.asc())
            .all()
        )

        results: list[dict[str, Any]] = []
        now = datetime.now(UTC)

        for loan in active_loans:
            book = db.query(Book).filter(Book.id == loan.book_id).first()
            due_dt = (
                loan.due_date
                if loan.due_date.tzinfo
                else loan.due_date.replace(tzinfo=UTC)
            )
            is_overdue = due_dt < now

            results.append(
                {
                    "loan_id": loan.id,
                    "book_id": loan.book_id,
                    "title": book.title if book else "Unknown Title",
                    "author": book.author if book else "Unknown Author",
                    "borrowed_at": loan.borrowed_at.strftime("%Y-%m-%d"),
                    "due_date": loan.due_date.strftime("%Y-%m-%d"),
                    "is_overdue": is_overdue,
                }
            )

        if results:
            ctx.deps.interactive_card = {
                "type": "ACTIVE_LOANS",
                "loans": results,
            }

        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="get_my_active_loans",
                arguments={},
                result=results,
            )
        )
        return results

    except Exception as exc:
        logger.error("Error executing get_my_active_loans tool: %s", exc, exc_info=True)
        err_res = [{"error": f"Failed to retrieve active loans: {exc}"}]
        ctx.deps.tools_executed.append(
            ToolExecutionRecord(
                tool_name="get_my_active_loans",
                arguments={},
                result=err_res,
            )
        )
        return err_res

