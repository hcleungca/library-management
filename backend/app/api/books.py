from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.db.session import get_db
from app.models.book import Book
from app.schemas.auth import TokenUser, UserRole
from app.schemas.book import BookCreate, BookListResponse, BookRead, BookUpdate

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
    query = db.query(Book)

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
            )
        )

    total = query.count()
    books = query.order_by(Book.id.asc()).offset(skip).limit(limit).all()

    return BookListResponse(
        items=[BookRead.model_validate(b) for b in books],
        total=total,
    )


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> BookRead:
    """Retrieve metadata and inventory status for a specific book by ID."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book #{book_id} not found",
        )
    return BookRead.model_validate(book)


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
    book = db.query(Book).filter(Book.id == book_id).first()
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
    """Delete a book record from the catalog (Librarian only)."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book #{book_id} not found",
        )

    if book.status == "CHECKED_OUT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete book that is currently checked out by a patron",
        )

    db.delete(book)
    db.commit()

