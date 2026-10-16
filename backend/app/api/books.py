from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.db.session import get_db
from app.models.book import Book
from app.models.loan import Loan
from app.schemas.auth import TokenUser, UserRole
from app.schemas.book import (
    BookCreate,
    BookListResponse,
    BookRead,
    BookStatus,
    BookUpdate,
)
from app.services.embedding_service import generate_embedding

router = APIRouter(prefix="/books", tags=["Books"])
librarian_guard = require_role(UserRole.LIBRARIAN)


@router.get("", response_model=BookListResponse)
def list_books(
    genre: str | None = None,
    status: str | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BookListResponse:
    """Retrieve a paginated and filtered list of books from the catalog."""
    query = db.query(Book).filter(Book.status != "DECOMMISSIONED")

    if genre:
        query = query.filter(Book.genre.ilike(f"%{genre}%"))

    if status:
        query = query.filter(Book.status == status.upper())

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.ilike(search_pattern),
                Book.author.ilike(search_pattern),
                Book.summary.ilike(search_pattern),
            )
        )

    total = query.count()
    books = query.order_by(Book.id.asc()).offset(skip).limit(limit).all()

    # Verify active loans for accurate circulation status
    book_ids = [b.id for b in books]
    active_loan_book_ids: set[int] = set()
    if book_ids:
        from app.models.loan import Loan

        active_loans = (
            db.query(Loan.book_id)
            .filter(Loan.book_id.in_(book_ids), Loan.status == "ACTIVE")
            .all()
        )
        active_loan_book_ids = {row[0] for row in active_loans}

    items: list[BookRead] = []
    needs_commit = False
    for b in books:
        book_dto = BookRead.model_validate(b)
        if b.id in active_loan_book_ids:
            if book_dto.status != BookStatus.CHECKED_OUT:
                book_dto.status = BookStatus.CHECKED_OUT
                b.status = "CHECKED_OUT"
                needs_commit = True
        items.append(book_dto)

    if needs_commit:
        try:
            db.commit()
        except Exception:
            db.rollback()

    return BookListResponse(
        items=items,
        total=total,
    )


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> BookRead:
    """Retrieve metadata and inventory status for a specific book by ID."""
    book = (
        db.query(Book)
        .filter(Book.id == book_id, Book.status != "DECOMMISSIONED")
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book #{book_id} not found",
        )

    from app.models.loan import Loan

    active_loan = (
        db.query(Loan)
        .filter(Loan.book_id == book.id, Loan.status == "ACTIVE")
        .first()
    )
    book_dto = BookRead.model_validate(book)
    if active_loan and book_dto.status != BookStatus.CHECKED_OUT:
        book_dto.status = BookStatus.CHECKED_OUT
        book.status = "CHECKED_OUT"
        try:
            db.commit()
        except Exception:
            db.rollback()

    return book_dto


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    book_in: BookCreate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(librarian_guard),
) -> BookRead:
    """Catalog a new book inventory asset (Librarian only)."""
    if book_in.isbn:
        existing = db.query(Book).filter(Book.isbn == book_in.isbn).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book with ISBN '{book_in.isbn}' already exists",
            )

    book = Book(**book_in.model_dump())
    embed_text = f"{book.title} {book.author} {book.genre or ''} {book.summary or ''}".strip()
    if embed_text:
        book.embedding = generate_embedding(embed_text)

    db.add(book)
    db.commit()
    db.refresh(book)
    return BookRead.model_validate(book)


@router.patch("/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    book_in: BookUpdate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(librarian_guard),
) -> BookRead:
    """Partially update an existing book's metadata (Librarian only)."""
    book = (
        db.query(Book)
        .filter(Book.id == book_id, Book.status != "DECOMMISSIONED")
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book #{book_id} not found",
        )

    update_data = book_in.model_dump(exclude_unset=True)

    # Check ISBN uniqueness if updating ISBN
    if "isbn" in update_data and update_data["isbn"] != book.isbn:
        existing = (
            db.query(Book).filter(Book.isbn == update_data["isbn"]).first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ISBN '{update_data['isbn']}' already in use",
            )

    # If status enum passed, convert to string
    if "status" in update_data and hasattr(update_data["status"], "value"):
        update_data["status"] = update_data["status"].value

    for field, val in update_data.items():
        setattr(book, field, val)

    # Recompute embedding if descriptive text fields changed or embedding is missing
    content_fields = {"title", "author", "genre", "summary"}
    if book.embedding is None or content_fields.intersection(update_data.keys()):
        embed_text = f"{book.title} {book.author} {book.genre or ''} {book.summary or ''}".strip()
        if embed_text:
            book.embedding = generate_embedding(embed_text)

    book.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(book)
    return BookRead.model_validate(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(librarian_guard),
) -> None:
    """Delete a book record from the catalog (Librarian only).

    - Mistakenly added books (zero loan history) are permanently hard-deleted, freeing their ISBN.
    - Books with past loan history are soft-deleted (status='DECOMMISSIONED', ISBN freed) to preserve circulation audits.
    - Books with active loans (currently checked out) cannot be deleted.
    """
    # Acquire exclusive DB row lock on the book to prevent concurrent checkout/return races
    book = (
        db.query(Book)
        .filter(Book.id == book_id, Book.status != "DECOMMISSIONED")
        .with_for_update()
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book #{book_id} not found",
        )

    # 1. Active loans are protected
    active_loan = (
        db.query(Loan)
        .filter(Loan.book_id == book_id, Loan.status == "ACTIVE")
        .first()
    )
    if book.status == "CHECKED_OUT" or active_loan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete book that is currently checked out by a patron",
        )

    # 2. Check for past circulation history
    has_loan_history = (
        db.query(Loan)
        .filter(Loan.book_id == book_id)
        .first()
        is not None
    )

    if has_loan_history:
        # Soft delete: Decommission volume to preserve loan history, free up ISBN
        if book.isbn:
            orig_isbn = book.isbn
            book.summary = (
                f"[Decommissioned Volume - Former ISBN: {orig_isbn}]\n{book.summary or ''}"
            ).strip()
            book.isbn = None
        book.status = "DECOMMISSIONED"
        embed_text = f"{book.title} {book.author} {book.genre or ''} {book.summary or ''}".strip()
        if embed_text:
            book.embedding = generate_embedding(embed_text)
        book.updated_at = datetime.now(UTC)
        db.commit()
    else:
        # Hard delete: Mistakenly added book with no circulation history
        db.delete(book)
        db.commit()

