import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.book import Book


class MaintenanceLog(Base):
    """Reverse logistics maintenance and damage triage log model.

    Records physical damage inspection notes, severity classification,
    recommended conservation protocols, and repair resolution state.
    """

    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    logged_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id"),
        nullable=False,
    )
    damage_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        default="MODERATE",
        nullable=False,
    )
    recommended_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    book: Mapped["Book"] = relationship(
        "Book",
        back_populates="maintenance_logs",
    )

