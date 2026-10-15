"""Database seeding execution script.

Provisions demo user accounts, catalogs the 15 curated seed books,
creates active loan records (including overdue items), and generates
maintenance triage logs for physical inventory lifecycle demonstration.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.models import Book, Loan, MaintenanceLog, Profile
from scripts.seed_data import SEED_BOOKS


def get_or_create_profile(
    db,
    email: str,
    full_name: str,
    role: str,
) -> Profile:
    """Fetch an existing profile by email or create a new one idempotently."""
    profile = db.query(Profile).filter(Profile.email == email).first()
    if not profile:
        profile = Profile(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            role=role,
        )
        db.add(profile)
        db.flush()
    return profile


def seed_database() -> dict[str, int]:
    """Execute idempotent database seeding."""
    db = SessionLocal()
    summary = {
        "profiles": 0,
        "books": 0,
        "loans": 0,
        "maintenance_logs": 0,
    }

    try:
        # 1. Provision Demo Accounts
        patron = get_or_create_profile(
            db,
            email="patron@example.com",
            full_name="Demo Patron",
            role="PATRON",
        )
        librarian = get_or_create_profile(
            db,
            email="librarian@example.com",
            full_name="Demo Librarian",
            role="LIBRARIAN",
        )
        db.flush()
        summary["profiles"] = 2

        now = datetime.now(UTC)

        # 2. Seed Books and Associated Workflow Records
        for book_data in SEED_BOOKS:
            isbn = book_data["isbn"]
            book = db.query(Book).filter(Book.isbn == isbn).first()

            if not book:
                book = Book(
                    title=book_data["title"],
                    author=book_data["author"],
                    isbn=isbn,
                    genre=book_data["genre"],
                    publication_year=book_data["publication_year"],
                    dewey_decimal=book_data["dewey_decimal"],
                    summary=book_data["summary"],
                    cover_image_url=book_data["cover_image_url"],
                    status=book_data["status"],
                )
                db.add(book)
                db.flush()
            else:
                # Update existing book record to match seed definition
                book.title = book_data["title"]
                book.author = book_data["author"]
                book.genre = book_data["genre"]
                book.publication_year = book_data["publication_year"]
                book.dewey_decimal = book_data["dewey_decimal"]
                book.summary = book_data["summary"]
                book.cover_image_url = book_data["cover_image_url"]
                book.status = book_data["status"]
                db.flush()

            summary["books"] += 1

            # 3. Create active loans for CHECKED_OUT books
            if book.status == "CHECKED_OUT":
                active_loan = (
                    db.query(Loan)
                    .filter(Loan.book_id == book.id, Loan.status == "ACTIVE")
                    .first()
                )
                if not active_loan:
                    if book_data.get("is_overdue"):
                        # Past due date (e.g. 7 days ago) to trigger OVERDUE status
                        borrowed_at = now - timedelta(days=21)
                        due_date = now - timedelta(days=7)
                    else:
                        borrowed_at = now - timedelta(days=2)
                        due_date = now + timedelta(days=12)

                    loan = Loan(
                        book_id=book.id,
                        user_id=patron.id,
                        borrowed_at=borrowed_at,
                        due_date=due_date,
                        status="ACTIVE",
                    )
                    db.add(loan)
                    db.flush()
                summary["loans"] += 1

            # 4. Create maintenance logs for IN_MAINTENANCE books
            if book.status == "IN_MAINTENANCE":
                existing_log = (
                    db.query(MaintenanceLog)
                    .filter(
                        MaintenanceLog.book_id == book.id,
                        MaintenanceLog.resolved_at.is_(None),
                    )
                    .first()
                )
                if not existing_log:
                    log = MaintenanceLog(
                        book_id=book.id,
                        logged_by=librarian.id,
                        damage_description=book_data.get(
                            "initial_damage_note",
                            "Flagged during intake inspection for conservation repair.",
                        ),
                        severity="MODERATE",
                    )
                    db.add(log)
                    db.flush()
                summary["maintenance_logs"] += 1

        db.commit()

        print("=" * 60)
        print("Database Seeding Completed Successfully:")
        print(f"  • Profiles verified/created : {summary['profiles']}")
        print(f"  • Books cataloged           : {summary['books']}")
        print(f"  • Active loans provisioned  : {summary['loans']}")
        print(f"  • Maintenance logs recorded : {summary['maintenance_logs']}")
        print("=" * 60)

        return summary

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
