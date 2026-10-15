from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.book import (
    BookBase,
    BookCreate,
    BookListResponse,
    BookRead,
    BookStatus,
    BookUpdate,
)


def test_book_status_enum():
    """Verify all 3 reverse logistics lifecycle statuses exist."""
    assert BookStatus.AVAILABLE == "AVAILABLE"
    assert BookStatus.CHECKED_OUT == "CHECKED_OUT"
    assert BookStatus.IN_PROCESSING == "IN_PROCESSING"


def test_book_create_valid_and_defaults():
    """Verify BookCreate with valid fields and default status."""
    book = BookCreate(
        title="Designing Data-Intensive Applications",
        author="Martin Kleppmann",
        isbn="9781449373320",
        genre="Distributed Systems",
        publication_year=2017,
        dewey_decimal="005.7",
        summary="A comprehensive guide to data systems architecture.",
        cover_image_url="https://covers.openlibrary.org/b/isbn/9781449373320-L.jpg",
    )
    assert book.title == "Designing Data-Intensive Applications"
    assert book.author == "Martin Kleppmann"
    assert book.status == BookStatus.AVAILABLE
    assert book.publication_year == 2017


def test_book_create_validation_errors():
    """Verify validation constraints on title, author, and publication year."""
    # Empty title
    with pytest.raises(ValidationError):
        BookCreate(title="", author="Author Name")

    # Empty author
    with pytest.raises(ValidationError):
        BookCreate(title="Valid Title", author="")

    # Year too early (< 1000)
    with pytest.raises(ValidationError):
        BookCreate(title="Ancient", author="Scribe", publication_year=999)

    # Year too far in future (> 2100)
    with pytest.raises(ValidationError):
        BookCreate(title="Future", author="Cyborg", publication_year=3000)

    # Invalid status
    with pytest.raises(ValidationError):
        BookCreate(title="Title", author="Author", status="LOST")  # type: ignore[arg-type]


def test_book_update_optional_fields():
    """Verify BookUpdate permits partial and empty updates."""
    empty_update = BookUpdate()
    assert empty_update.title is None
    assert empty_update.status is None

    partial_update = BookUpdate(title="Updated Title", status=BookStatus.IN_PROCESSING)
    assert partial_update.title == "Updated Title"
    assert partial_update.status == BookStatus.IN_PROCESSING


def test_book_read_from_attributes():
    """Verify BookRead instantiates from ORM model attributes."""
    now = datetime.now(UTC)

    class MockBookModel:
        id = 42
        title = "Clean Code"
        author = "Robert C. Martin"
        isbn = "9780132350884"
        genre = "Software Engineering"
        publication_year = 2008
        dewey_decimal = "005.1"
        summary = "Handbook of Agile Software Craftsmanship"
        cover_image_url = None
        status = "AVAILABLE"
        created_at = now
        updated_at = now

    mock_book = MockBookModel()
    book_read = BookRead.model_validate(mock_book)

    assert book_read.id == 42
    assert book_read.title == "Clean Code"
    assert book_read.author == "Robert C. Martin"
    assert book_read.status == BookStatus.AVAILABLE
    assert book_read.created_at == now


def test_book_list_response_envelope():
    """Verify BookListResponse wraps items and total count."""
    now = datetime.now(UTC)
    item = BookRead(
        id=1,
        title="Refactoring",
        author="Martin Fowler",
        status=BookStatus.AVAILABLE,
        created_at=now,
        updated_at=now,
    )
    response = BookListResponse(items=[item], total=1)
    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].id == 1


def test_total_copies_omitted():
    """Verify total_copies is omitted from book schemas to maintain physical asset 1:1 model."""
    assert "total_copies" not in BookBase.model_fields
    assert "total_copies" not in BookCreate.model_fields
    assert "total_copies" not in BookUpdate.model_fields
    assert "total_copies" not in BookRead.model_fields
