"""Circulation API router for book checkout, return, and loan management."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_role
from app.db.session import get_db
from app.models.book import Book
from app.models.loan import Loan
from app.models.profile import Profile
from app.schemas.auth import TokenUser, UserRole
from app.schemas.book import BookRead
from app.schemas.loan import CheckoutRequest, LoanRead, LoanWithBookRead

router = APIRouter(prefix="/circulation", tags=["Circulation"])
librarian_guard = require_role(UserRole.LIBRARIAN)


@router.post(
    "/checkout", response_model=LoanRead, status_code=status.HTTP_201_CREATED
)
def checkout_book(
    req: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
) -> LoanRead:
    """Check out an available book to the authenticated patron with concurrency protection."""
    if current_user.role != UserRole.PATRON:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patrons are permitted to check out books. Staff and librarians cannot borrow books.",
        )

    # Concurrency Protection: Acquire exclusive row-level lock on the book row
    book = (
        db.query(Book)
        .filter(Book.id == req.book_id)
        .with_for_update()
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book #{req.book_id} not found",
        )

    # If another concurrent request just modified the status, reject with 409 Conflict
    if book.status != "AVAILABLE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Book '{book.title}' is not available for checkout (current"
                f" status: {book.status})"
            ),
        )

    # Ensure no active loan already exists for this physical book
    active_loan = (
        db.query(Loan)
        .filter(Loan.book_id == book.id, Loan.status == "ACTIVE")
        .first()
    )
    if active_loan:
        if book.status != "CHECKED_OUT":
            book.status = "CHECKED_OUT"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Book '{book.title}' has already been checked out under active"
                f" loan #{active_loan.id}."
            ),
        )

    # State transition: AVAILABLE -> CHECKED_OUT
    book.status = "CHECKED_OUT"
    now = datetime.now(UTC)
    due_date = now + timedelta(days=req.loan_duration_days)

    loan = Loan(
        book_id=book.id,
        user_id=current_user.id,
        borrowed_at=now,
        due_date=due_date,
        status="ACTIVE",
    )
    db.add(loan)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrent checkout conflict detected. This book has already been checked out.",
        )

    db.refresh(loan)
    return loan


@router.post("/return/{loan_id}", response_model=LoanRead)
def return_book(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
) -> LoanRead:
    """Discharge an active loan and transition the book to IN_PROCESSING reverse logistics."""
    # Concurrency Protection: Acquire exclusive row-level lock on the loan
    loan = (
        db.query(Loan)
        .filter(Loan.id == loan_id)
        .with_for_update()
        .first()
    )
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan #{loan_id} not found",
        )

    # Only borrower or librarian can process return
    if (
        loan.user_id != current_user.id
        and current_user.role != UserRole.LIBRARIAN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to return another patron's book",
        )

    if loan.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This loan is already returned",
        )

    # Discharge loan
    loan.status = "RETURNED"
    loan.returned_at = datetime.now(UTC)

    # Core Reverse Logistics Transition: CHECKED_OUT -> IN_PROCESSING (with row lock)
    book = (
        db.query(Book)
        .filter(Book.id == loan.book_id)
        .with_for_update()
        .first()
    )
    if book:
        book.status = "IN_PROCESSING"

    db.commit()
    db.refresh(loan)
    return loan


@router.get("/my-loans", response_model=list[LoanWithBookRead])
def get_my_loans(
    status_filter: str | None = None,  # 'ACTIVE' | 'RETURNED'
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
) -> list[LoanWithBookRead]:
    """Retrieve the authenticated patron's loan history with book details and overdue computation."""
    query = (
        db.query(Loan, Book)
        .join(Book, Loan.book_id == Book.id)
        .filter(Loan.user_id == current_user.id)
    )

    if status_filter:
        query = query.filter(Loan.status == status_filter.upper())

    results = query.order_by(Loan.borrowed_at.desc()).all()
    now = datetime.now(UTC)

    response = []
    for loan, book in results:
        comp_now = now if loan.due_date.tzinfo is not None else datetime.now()
        is_overdue = loan.status == "ACTIVE" and loan.due_date < comp_now
        response.append(
            LoanWithBookRead(
                id=loan.id,
                book_id=loan.book_id,
                user_id=loan.user_id,
                borrowed_at=loan.borrowed_at,
                due_date=loan.due_date,
                returned_at=loan.returned_at,
                status=loan.status,
                is_overdue=is_overdue,
                book_title=book.title,
                book_author=book.author,
                cover_image_url=book.cover_image_url,
            )
        )
    return response


@router.get("/loans", response_model=list[LoanWithBookRead])
def get_all_active_loans(
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(librarian_guard),
) -> list[LoanWithBookRead]:
    """Retrieve all system-wide active loans with patron details and overdue indicators (Librarian only)."""
    query = (
        db.query(Loan, Book, Profile)
        .join(Book, Loan.book_id == Book.id)
        .join(Profile, Loan.user_id == Profile.id)
        .filter(Loan.status == "ACTIVE")
    )

    now = datetime.now(UTC)
    if overdue_only:
        query = query.filter(Loan.due_date < now)

    results = query.order_by(Loan.due_date.asc()).all()

    response = []
    for loan, book, profile in results:
        comp_now = now if loan.due_date.tzinfo is not None else datetime.now()
        is_overdue = loan.due_date < comp_now
        response.append(
            LoanWithBookRead(
                id=loan.id,
                book_id=loan.book_id,
                user_id=loan.user_id,
                borrowed_at=loan.borrowed_at,
                due_date=loan.due_date,
                returned_at=loan.returned_at,
                status=loan.status,
                is_overdue=is_overdue,
                book_title=book.title,
                book_author=book.author,
                cover_image_url=book.cover_image_url,
                patron_email=profile.email,
            )
        )
    return response


@router.get("/intake", response_model=list[BookRead])
def get_intake_queue(
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(librarian_guard),
) -> list[BookRead]:
    """Retrieve books in IN_PROCESSING awaiting intake shelving (Librarian only)."""
    return (
        db.query(Book)
        .filter(Book.status == "IN_PROCESSING")
        .order_by(Book.updated_at.asc())
        .all()
    )


@router.post("/shelve/{book_id}", response_model=BookRead)
def shelve_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(librarian_guard),
) -> BookRead:
    """Transition a book from IN_PROCESSING back to AVAILABLE with concurrency protection (Librarian only)."""
    # Concurrency Protection: Acquire exclusive row-level lock on the book row
    book = (
        db.query(Book)
        .filter(Book.id == book_id)
        .with_for_update()
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book #{book_id} not found",
        )

    if book.status != "IN_PROCESSING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot shelve book with status '{book.status}'. Only items in"
                " 'IN_PROCESSING' can be shelved."
            ),
        )

    # State transition: IN_PROCESSING -> AVAILABLE
    book.status = "AVAILABLE"
    book.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(book)
    return book

