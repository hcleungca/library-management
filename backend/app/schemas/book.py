"""Book catalog and inventory Pydantic schemas.

Defines schemas for book creation, updates, and serialized responses,
including validation rules for ISBN, lifecycle status enums, publication year,
and Dewey Decimal classification.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class BookStatus(str, Enum):
    """Lifecycle status of a physical book asset in the reverse logistics workflow."""

    AVAILABLE = "AVAILABLE"
    CHECKED_OUT = "CHECKED_OUT"
    IN_PROCESSING = "IN_PROCESSING"
    DECOMMISSIONED = "DECOMMISSIONED"


class BookBase(BaseModel):
    """Base book schema with core metadata attributes."""

    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str | None = Field(None, max_length=32)
    genre: str | None = Field(None, max_length=100)
    publication_year: int | None = Field(None, ge=1000, le=2100)
    dewey_decimal: str | None = Field(None, max_length=32)
    summary: str | None = None
    cover_image_url: str | None = None


class BookCreate(BookBase):
    """Schema for creating a new catalog book asset."""

    status: BookStatus = BookStatus.AVAILABLE


class BookUpdate(BaseModel):
    """Schema for partial book metadata updates."""

    title: str | None = Field(None, min_length=1, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    isbn: str | None = Field(None, max_length=32)
    genre: str | None = Field(None, max_length=100)
    publication_year: int | None = Field(None, ge=1000, le=2100)
    dewey_decimal: str | None = Field(None, max_length=32)
    summary: str | None = None
    cover_image_url: str | None = None
    status: BookStatus | None = None


class BookRead(BookBase):
    """Schema for serialized book catalog item."""

    # Enable attribute-based mapping to allow direct instantiation from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: BookStatus
    created_at: datetime
    updated_at: datetime


class BookListResponse(BaseModel):
    """Paginated book list response envelope."""

    items: list[BookRead]
    total: int

