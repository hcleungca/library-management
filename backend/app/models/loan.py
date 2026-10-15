import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.profile import Profile


class Loan(Base):
    """Circulation loan ORM model tracking patron borrowing history.

    Links patrons with book copies, enforces due dates, and records returns.
    """

    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        nullable=False,
    )

    # Relationships
    book: Mapped["Book"] = relationship(
        "Book",
        back_populates="loans",
    )
    user: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="loans",
    )

