"""Unit tests for circulation loan Pydantic schemas."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.loan import CheckoutRequest, LoanRead, LoanWithBookRead


class MockLoanORM:
    """Mock SQLAlchemy Loan model instance for testing from_attributes."""

    def __init__(
        self,
        id: int,
        book_id: int,
        user_id: uuid.UUID,
        borrowed_at: datetime,
        due_date: datetime,
        returned_at: datetime | None = None,
        status: str = "ACTIVE",
    ):
        self.id = id
        self.book_id = book_id
        self.user_id = user_id
        self.borrowed_at = borrowed_at
        self.due_date = due_date
        self.returned_at = returned_at
        self.status = status


def test_checkout_request_default_duration():
    """Verify CheckoutRequest defaults loan_duration_days to 14."""
    req = CheckoutRequest(book_id=42)
    assert req.book_id == 42
    assert req.loan_duration_days == 14


def test_checkout_request_valid_custom_duration():
    """Verify custom loan duration between 1 and 60 days is valid."""
    req_min = CheckoutRequest(book_id=1, loan_duration_days=1)
    assert req_min.loan_duration_days == 1

    req_max = CheckoutRequest(book_id=1, loan_duration_days=60)
    assert req_max.loan_duration_days == 60


@pytest.mark.parametrize("invalid_days", [0, -5, 61, 100])
def test_checkout_request_invalid_duration(invalid_days: int):
    """Verify loan_duration_days outside [1, 60] raises ValidationError."""
    with pytest.raises(ValidationError):
        CheckoutRequest(book_id=1, loan_duration_days=invalid_days)


def test_checkout_request_missing_book_id():
    """Verify missing book_id raises ValidationError."""
    with pytest.raises(ValidationError):
        CheckoutRequest.model_validate({})


def test_loan_read_active_not_overdue():
    """Verify active loan with future due date has is_overdue=False."""
    now = datetime.now(UTC)
    future_date = now + timedelta(days=14)
    user_id = uuid.uuid4()

    loan = LoanRead(
        id=1,
        book_id=10,
        user_id=user_id,
        borrowed_at=now,
        due_date=future_date,
        status="ACTIVE",
    )
    assert loan.id == 1
    assert loan.book_id == 10
    assert loan.user_id == user_id
    assert loan.returned_at is None
    assert loan.status == "ACTIVE"
    assert loan.is_overdue is False


def test_loan_read_active_overdue():
    """Verify active loan with past due date dynamically computes is_overdue=True."""
    now = datetime.now(UTC)
    past_date = now - timedelta(days=2)
    user_id = uuid.uuid4()

    loan = LoanRead(
        id=2,
        book_id=10,
        user_id=user_id,
        borrowed_at=past_date - timedelta(days=14),
        due_date=past_date,
        status="ACTIVE",
    )
    assert loan.is_overdue is True


def test_loan_read_returned_not_overdue():
    """Verify returned loan with past due date does not flag as overdue."""
    now = datetime.now(UTC)
    past_date = now - timedelta(days=5)
    user_id = uuid.uuid4()

    loan = LoanRead(
        id=3,
        book_id=10,
        user_id=user_id,
        borrowed_at=past_date - timedelta(days=14),
        due_date=past_date,
        returned_at=now,
        status="RETURNED",
    )
    assert loan.is_overdue is False


def test_loan_read_from_attributes():
    """Verify LoanRead can be instantiated from an ORM-like object."""
    now = datetime.now(UTC)
    due_date = now + timedelta(days=14)
    user_id = uuid.uuid4()

    orm_loan = MockLoanORM(
        id=100,
        book_id=20,
        user_id=user_id,
        borrowed_at=now,
        due_date=due_date,
        status="ACTIVE",
    )

    loan = LoanRead.model_validate(orm_loan)
    assert loan.id == 100
    assert loan.book_id == 20
    assert loan.user_id == user_id
    assert loan.status == "ACTIVE"
    assert loan.is_overdue is False


def test_loan_with_book_read():
    """Verify LoanWithBookRead includes book details and optional fields."""
    now = datetime.now(UTC)
    user_id = uuid.uuid4()

    loan = LoanWithBookRead(
        id=5,
        book_id=12,
        user_id=user_id,
        borrowed_at=now,
        due_date=now + timedelta(days=7),
        status="ACTIVE",
        book_title="Refactoring",
        book_author="Martin Fowler",
        cover_image_url="https://example.com/cover.jpg",
        patron_email="patron@example.com",
    )
    assert loan.book_title == "Refactoring"
    assert loan.book_author == "Martin Fowler"
    assert loan.cover_image_url == "https://example.com/cover.jpg"
    assert loan.patron_email == "patron@example.com"
    assert loan.is_overdue is False

    # Optional fields default to None
    loan_minimal = LoanWithBookRead(
        id=6,
        book_id=12,
        user_id=user_id,
        borrowed_at=now,
        due_date=now + timedelta(days=7),
        status="ACTIVE",
        book_title="Refactoring",
        book_author="Martin Fowler",
    )
    assert loan_minimal.cover_image_url is None
    assert loan_minimal.patron_email is None
