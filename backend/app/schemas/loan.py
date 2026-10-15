"""Circulation loan Pydantic schemas.

Defines schemas for book checkout requests, loan entity serialization,
and enriched loan responses including book and patron metadata.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CheckoutRequest(BaseModel):
    """Request payload to borrow a book."""

    book_id: int
    loan_duration_days: int = Field(14, ge=1, le=60)


class LoanRead(BaseModel):
    """Serialized circulation loan record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    user_id: UUID
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None = None
    status: str  # 'ACTIVE' | 'RETURNED'
    is_overdue: bool = False

    @model_validator(mode="after")
    def compute_overdue(self) -> "LoanRead":
        """Dynamically compute overdue status for active loans whose due date is in the past."""
        if not self.is_overdue and self.status == "ACTIVE" and self.due_date:
            now = (
                datetime.now(self.due_date.tzinfo)
                if self.due_date.tzinfo is not None
                else datetime.now()
            )
            if self.due_date < now:
                self.is_overdue = True
        return self


class LoanWithBookRead(LoanRead):
    """Enriched circulation loan record including book and patron metadata."""

    book_title: str
    book_author: str
    cover_image_url: str | None = None
    patron_email: str | None = None

