"""Unit tests for AI Librarian PydanticAI tools."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
import uuid

import pytest
from pydantic_ai import RunContext

from app.models.book import Book
from app.models.loan import Loan
from app.schemas.search import SearchResultBook
from app.services.agent_tools import (
    LibraryContext,
    borrow_book,
    check_availability,
    get_my_active_loans,
    search_catalog,
)


def create_mock_run_context(db: MagicMock, user_id: uuid.UUID | None = None) -> RunContext[LibraryContext]:
    """Helper to instantiate a mock RunContext with LibraryContext."""
    deps = LibraryContext(
        db=db,
        user_id=user_id or uuid.uuid4(),
        tools_executed=[],
        interactive_card=None,
    )
    mock_ctx = MagicMock(spec=RunContext)
    mock_ctx.deps = deps
    return mock_ctx


@patch("app.services.agent_tools.search_books_semantic")
def test_search_catalog_tool(mock_search_semantic):
    """Verify search_catalog formats results, records audit, and sets BOOK_LIST card."""
    mock_db = MagicMock()
    ctx = create_mock_run_context(mock_db)

    b1 = SearchResultBook(
        id=4,
        title="Database Internals",
        author="Alex Petrov",
        isbn="9781492040347",
        genre="Database Systems",
        publication_year=2019,
        dewey_decimal="005.74",
        summary="A deep dive into distributed systems and storage engines.",
        cover_image_url=None,
        status="AVAILABLE",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        similarity_score=0.74,
        cosine_distance=0.26,
    )
    b2 = SearchResultBook(
        id=6,
        title="Building Microservices",
        author="Sam Newman",
        isbn="9781492034025",
        genre="Microservices & Cloud",
        publication_year=2021,
        dewey_decimal="004.65",
        summary="Designing fine-grained systems.",
        cover_image_url=None,
        status="AVAILABLE",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        similarity_score=0.70,
        cosine_distance=0.30,
    )
    mock_search_semantic.return_value = [b1, b2]

    results = search_catalog(ctx, query="distributed databases")

    assert len(results) == 2
    assert results[0]["id"] == 4
    assert results[0]["title"] == "Database Internals"
    assert len(ctx.deps.tools_executed) == 1
    assert ctx.deps.tools_executed[0].tool_name == "search_catalog"
    assert ctx.deps.interactive_card["type"] == "BOOK_LIST"
    assert len(ctx.deps.interactive_card["books"]) == 2


def test_check_availability_available():
    """Verify check_availability sets CONFIRM_BORROW card when book is AVAILABLE."""
    mock_db = MagicMock()
    ctx = create_mock_run_context(mock_db)

    book = Book(
        id=4,
        title="Database Internals",
        author="Alex Petrov",
        status="AVAILABLE",
        cover_image_url="https://example.com/cover.jpg",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = book

    res = check_availability(ctx, book_id=4)

    assert res["found"] is True
    assert res["is_available"] is True
    assert ctx.deps.interactive_card is not None
    assert ctx.deps.interactive_card["type"] == "CONFIRM_BORROW"
    assert ctx.deps.interactive_card["book_id"] == 4
    assert ctx.deps.interactive_card["title"] == "Database Internals"
    assert len(ctx.deps.tools_executed) == 1
    assert ctx.deps.tools_executed[0].tool_name == "check_availability"


def test_check_availability_checked_out():
    """Verify check_availability does not set CONFIRM_BORROW card when book is CHECKED_OUT."""
    mock_db = MagicMock()
    ctx = create_mock_run_context(mock_db)

    book = Book(
        id=1,
        title="Designing Data-Intensive Applications",
        author="Martin Kleppmann",
        status="CHECKED_OUT",
        cover_image_url=None,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = book

    res = check_availability(ctx, book_id=1)

    assert res["found"] is True
    assert res["is_available"] is False
    assert ctx.deps.interactive_card is None


def test_borrow_book_success():
    """Verify borrow_book checks out book and sets LOAN_RECEIPT card."""
    mock_db = MagicMock()
    patron_id = uuid.uuid4()
    ctx = create_mock_run_context(mock_db, user_id=patron_id)

    book = Book(
        id=4,
        title="Database Internals",
        author="Alex Petrov",
        status="AVAILABLE",
        cover_image_url=None,
    )
    # Book query with_for_update returns book
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.with_for_update.return_value.first.return_value = book
    # Loan query filter returns None (no active loan)
    mock_query.filter.return_value.first.return_value = None

    res = borrow_book(ctx, book_id=4)

    assert res["success"] is True
    assert book.status == "CHECKED_OUT"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert ctx.deps.interactive_card["type"] == "LOAN_RECEIPT"
    assert ctx.deps.interactive_card["book_id"] == 4


def test_borrow_book_unavailable():
    """Verify borrow_book fails gracefully when book is not AVAILABLE."""
    mock_db = MagicMock()
    ctx = create_mock_run_context(mock_db)

    book = Book(
        id=4,
        title="Database Internals",
        author="Alex Petrov",
        status="CHECKED_OUT",
    )
    mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = book

    res = borrow_book(ctx, book_id=4)

    assert res["success"] is False
    assert "cannot be checked out" in res["error"]
    mock_db.add.assert_not_called()


def test_get_my_active_loans():
    """Verify get_my_active_loans retrieves user loans and sets ACTIVE_LOANS card."""
    mock_db = MagicMock()
    patron_id = uuid.uuid4()
    ctx = create_mock_run_context(mock_db, user_id=patron_id)

    now = datetime.now(UTC)
    loan1 = Loan(
        id=101,
        book_id=4,
        user_id=patron_id,
        borrowed_at=now - timedelta(days=2),
        due_date=now + timedelta(days=12),
        status="ACTIVE",
    )
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [loan1]

    book = Book(id=4, title="Database Internals", author="Alex Petrov")
    mock_db.query.return_value.filter.return_value.first.return_value = book

    results = get_my_active_loans(ctx)

    assert len(results) == 1
    assert results[0]["book_id"] == 4
    assert results[0]["title"] == "Database Internals"
    assert results[0]["is_overdue"] is False
    assert ctx.deps.interactive_card["type"] == "ACTIVE_LOANS"


def test_check_availability_librarian_no_confirm_card():
    """Verify check_availability does not attach CONFIRM_BORROW card when user_role is LIBRARIAN."""
    mock_db = MagicMock()
    ctx = create_mock_run_context(mock_db)
    ctx.deps.user_role = "LIBRARIAN"

    book = Book(
        id=4,
        title="Database Internals",
        author="Alex Petrov",
        status="AVAILABLE",
        cover_image_url="https://example.com/cover.jpg",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = book

    res = check_availability(ctx, book_id=4)
    assert res["is_available"] is True
    # Card must not be attached for librarians
    assert ctx.deps.interactive_card is None


def test_borrow_book_librarian_rejected():
    """Verify borrow_book returns error and rejects checkout when user_role is LIBRARIAN."""
    mock_db = MagicMock()
    ctx = create_mock_run_context(mock_db)
    ctx.deps.user_role = "LIBRARIAN"

    res = borrow_book(ctx, book_id=4)
    assert res["success"] is False
    assert "Only patrons may borrow books" in res["error"]
    assert len(ctx.deps.tools_executed) == 1
    assert ctx.deps.tools_executed[0].tool_name == "borrow_book"


