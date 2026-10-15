from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.maintenance import MaintenanceLog

    from app.models.loan import Loan


class Book(Base):
    """Book catalog and physical inventory ORM model.

    Each row represents a discrete physical inventory copy tracked through
    the reverse logistics lifecycle (AVAILABLE, CHECKED_OUT, IN_PROCESSING, IN_MAINTENANCE).
    Includes a 1536-dimensional vector embedding for semantic search.
    """

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    author: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    isbn: Mapped[str | None] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=True,
    )
    genre: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    dewey_decimal: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    cover_image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="AVAILABLE",
        index=True,
        nullable=False,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    loans: Mapped[list["Loan"]] = relationship(
        "Loan",
        back_populates="book",
    )
    maintenance_logs: Mapped[list["MaintenanceLog"]] = relationship(
        "MaintenanceLog",
        back_populates="book",
    )

