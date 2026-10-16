"""Integration tests for circulation API endpoints (checkout, concurrency, and locking)."""

import concurrent.futures
import time
import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.auth import create_demo_jwt
from app.db.session import SessionLocal
from app.main import app
from app.models.book import Book
from app.models.loan import Loan
from app.schemas.auth import UserRole

client = TestClient(app)


def test_circulation_checkout_route_registered():
    """Verify /api/circulation/checkout route is registered in the FastAPI app."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/circulation/checkout" in openapi_paths
    assert "post" in openapi_paths["/api/circulation/checkout"]


def test_checkout_unauthenticated():
    """Verify checkout requires authentication and returns HTTP 401."""
    res = client.post("/api/circulation/checkout", json={"book_id": 1})
    assert res.status_code == 401


def test_checkout_librarian_forbidden():
    """Verify librarian attempting checkout is rejected with HTTP 403 Forbidden."""
    token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    res = client.post(
        "/api/circulation/checkout",
        json={"book_id": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "Only patrons are permitted to check out books" in res.json()["detail"]



def test_checkout_book_not_found():
    """Verify checkout of nonexistent book returns HTTP 404."""
    token, _ = create_demo_jwt(UserRole.PATRON)
    res = client.post(
        "/api/circulation/checkout",
        json={"book_id": 999999},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Book #999999 not found"


def test_checkout_book_not_available():
    """Verify checkout of non-AVAILABLE book returns HTTP 409 Conflict."""
    token, _ = create_demo_jwt(UserRole.PATRON)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    db = SessionLocal()
    book = Book(
        title="Unavailable Book",
        author="Author",
        isbn=isbn,
        status="IN_PROCESSING",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    try:
        res = client.post(
            "/api/circulation/checkout",
            json={"book_id": book_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 409
        assert "not available for checkout" in res.json()["detail"]
    finally:
        db = SessionLocal()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_checkout_book_success():
    """Verify successful checkout creates loan, mutates book status, and returns 201."""
    db = SessionLocal()
    token, user = create_demo_jwt(UserRole.PATRON, db=db)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    book = Book(
        title="Checkout Book",
        author="Author",
        isbn=isbn,
        status="AVAILABLE",
        publication_year=2020,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    loan_id = None
    try:
        res = client.post(
            "/api/circulation/checkout",
            json={"book_id": book_id, "loan_duration_days": 21},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["book_id"] == book_id
        assert data["status"] == "ACTIVE"
        assert data["is_overdue"] is False
        loan_id = data["id"]

        # Verify database state
        db = SessionLocal()
        db_book = db.query(Book).filter(Book.id == book_id).first()
        assert db_book.status == "CHECKED_OUT"

        db_loan = db.query(Loan).filter(Loan.id == loan_id).first()
        assert db_loan is not None
        assert str(db_loan.user_id) == str(user.id)
        assert db_loan.status == "ACTIVE"
        db.close()
    finally:
        db = SessionLocal()
        if loan_id:
            db.query(Loan).filter(Loan.id == loan_id).delete()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_concurrent_checkout_race_condition():
    """Verify two simultaneous checkouts for the same book resolve safely.

    Exactly one checkout succeeds with HTTP 201, while the competing checkout
    receives HTTP 409 Conflict.
    """
    db = SessionLocal()
    token_1, _ = create_demo_jwt(UserRole.PATRON, db=db)
    token_2, _ = create_demo_jwt(UserRole.PATRON, db=db)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    book = Book(
        title="Contested Book",
        author="Author",
        isbn=isbn,
        status="AVAILABLE",
        publication_year=2023,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    def perform_checkout(auth_token: str):
        c = TestClient(app)
        return c.post(
            "/api/circulation/checkout",
            json={"book_id": book_id, "loan_duration_days": 14},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_1 = executor.submit(perform_checkout, token_1)
            future_2 = executor.submit(perform_checkout, token_2)
            res_1 = future_1.result()
            res_2 = future_2.result()

        status_codes = sorted([res_1.status_code, res_2.status_code])
        assert status_codes == [201, 409], f"Expected [201, 409], got {status_codes}"

        # Verify DB state: exactly 1 active loan, book status CHECKED_OUT
        db = SessionLocal()
        active_loans = (
            db.query(Loan)
            .filter(Loan.book_id == book_id, Loan.status == "ACTIVE")
            .all()
        )
        assert len(active_loans) == 1

        db_book = db.query(Book).filter(Book.id == book_id).first()
        assert db_book.status == "CHECKED_OUT"
        db.close()
    finally:
        db = SessionLocal()
        db.query(Loan).filter(Loan.book_id == book_id).delete()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_circulation_return_route_registered():
    """Verify /api/circulation/return/{loan_id} route is registered in FastAPI app."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/circulation/return/{loan_id}" in openapi_paths
    assert "post" in openapi_paths["/api/circulation/return/{loan_id}"]


def test_return_book_not_found():
    """Verify return of nonexistent loan returns HTTP 404."""
    db = SessionLocal()
    token, _ = create_demo_jwt(UserRole.PATRON, db=db)
    db.close()

    res = client.post(
        "/api/circulation/return/999999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Loan #999999 not found"


def test_return_book_by_borrower_success():
    """Verify borrower can return their book, transitioning book to IN_PROCESSING."""
    db = SessionLocal()
    token, _ = create_demo_jwt(UserRole.PATRON, db=db)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    book = Book(
        title="Return Test Book",
        author="Author",
        isbn=isbn,
        status="AVAILABLE",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    loan_id = None
    try:
        # 1. Checkout book
        co_res = client.post(
            "/api/circulation/checkout",
            json={"book_id": book_id, "loan_duration_days": 14},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert co_res.status_code == 201
        loan_id = co_res.json()["id"]

        # 2. Return book
        ret_res = client.post(
            f"/api/circulation/return/{loan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ret_res.status_code == 200
        ret_data = ret_res.json()
        assert ret_data["id"] == loan_id
        assert ret_data["status"] == "RETURNED"
        assert ret_data["returned_at"] is not None

        # 3. Core Reverse Logistics verification: book status must be IN_PROCESSING
        db = SessionLocal()
        db_book = db.query(Book).filter(Book.id == book_id).first()
        assert db_book.status == "IN_PROCESSING"

        # 4. Attempting to return again must fail with HTTP 400
        dup_res = client.post(
            f"/api/circulation/return/{loan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dup_res.status_code == 400
        assert dup_res.json()["detail"] == "This loan is already returned"
        db.close()
    finally:
        db = SessionLocal()
        if loan_id:
            db.query(Loan).filter(Loan.id == loan_id).delete()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_return_book_permission_denied():
    """Verify non-borrower patron cannot return another patron's loan."""
    db = SessionLocal()
    borrower_token, _ = create_demo_jwt(UserRole.PATRON, db=db)
    # Token without DB has a different UUID
    other_patron_token, _ = create_demo_jwt(UserRole.PATRON)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    book = Book(
        title="Permission Book",
        author="Author",
        isbn=isbn,
        status="AVAILABLE",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    loan_id = None
    try:
        co_res = client.post(
            "/api/circulation/checkout",
            json={"book_id": book_id, "loan_duration_days": 14},
            headers={"Authorization": f"Bearer {borrower_token}"},
        )
        assert co_res.status_code == 201
        loan_id = co_res.json()["id"]

        # Other patron tries to return -> 403 Forbidden
        denied_res = client.post(
            f"/api/circulation/return/{loan_id}",
            headers={"Authorization": f"Bearer {other_patron_token}"},
        )
        assert denied_res.status_code == 403
        assert (
            denied_res.json()["detail"]
            == "You do not have permission to return another patron's book"
        )
    finally:
        db = SessionLocal()
        if loan_id:
            db.query(Loan).filter(Loan.id == loan_id).delete()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_return_book_by_librarian():
    """Verify librarian can return any patron's loan."""
    db = SessionLocal()
    patron_token, _ = create_demo_jwt(UserRole.PATRON, db=db)
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN, db=db)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    book = Book(
        title="Librarian Return Book",
        author="Author",
        isbn=isbn,
        status="AVAILABLE",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    loan_id = None
    try:
        co_res = client.post(
            "/api/circulation/checkout",
            json={"book_id": book_id, "loan_duration_days": 14},
            headers={"Authorization": f"Bearer {patron_token}"},
        )
        assert co_res.status_code == 201
        loan_id = co_res.json()["id"]

        # Librarian processes return
        lib_res = client.post(
            f"/api/circulation/return/{loan_id}",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert lib_res.status_code == 200
        assert lib_res.json()["status"] == "RETURNED"

        db = SessionLocal()
        db_book = db.query(Book).filter(Book.id == book_id).first()
        assert db_book.status == "IN_PROCESSING"
        db.close()
    finally:
        db = SessionLocal()
        if loan_id:
            db.query(Loan).filter(Loan.id == loan_id).delete()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_concurrent_return_race_condition():
    """Verify simultaneous returns on the same loan serialize safely with pessimistic locking.

    Exactly one return succeeds with HTTP 200, while the competing return
    receives HTTP 400 Bad Request ("This loan is already returned").
    """
    db = SessionLocal()
    patron_token, _ = create_demo_jwt(UserRole.PATRON, db=db)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    book = Book(
        title="Concurrent Return Book",
        author="Author",
        isbn=isbn,
        status="AVAILABLE",
        publication_year=2022,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    loan_id = None
    try:
        co_res = client.post(
            "/api/circulation/checkout",
            json={"book_id": book_id, "loan_duration_days": 14},
            headers={"Authorization": f"Bearer {patron_token}"},
        )
        assert co_res.status_code == 201
        loan_id = co_res.json()["id"]

        def perform_return():
            c = TestClient(app)
            return c.post(
                f"/api/circulation/return/{loan_id}",
                headers={"Authorization": f"Bearer {patron_token}"},
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(perform_return)
            f2 = executor.submit(perform_return)
            r1 = f1.result()
            r2 = f2.result()

        status_codes = sorted([r1.status_code, r2.status_code])
        assert status_codes == [200, 400], f"Expected [200, 400], got {status_codes}"

        db = SessionLocal()
        db_book = db.query(Book).filter(Book.id == book_id).first()
        assert db_book.status == "IN_PROCESSING"

        db_loan = db.query(Loan).filter(Loan.id == loan_id).first()
        assert db_loan.status == "RETURNED"
        assert db_loan.returned_at is not None
        db.close()
    finally:
        db = SessionLocal()
        if loan_id:
            db.query(Loan).filter(Loan.id == loan_id).delete()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_circulation_my_loans_route_registered():
    """Verify /api/circulation/my-loans route is registered in FastAPI app."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/circulation/my-loans" in openapi_paths
    assert "get" in openapi_paths["/api/circulation/my-loans"]


def test_my_loans_unauthenticated():
    """Verify GET /api/circulation/my-loans requires authentication."""
    res = client.get("/api/circulation/my-loans")
    assert res.status_code == 401


def test_my_loans_history_and_overdue_flag():
    """Verify patron can retrieve their loan history with overdue calculation and book details."""
    db = SessionLocal()
    token, user = create_demo_jwt(UserRole.PATRON, db=db)
    now = datetime.now(UTC)

    isbn_1 = f"978{int(time.time() * 1000)}"[:13]
    isbn_2 = f"979{int(time.time() * 1000)}"[:13]

    book_active = Book(
        title="Future Due Book",
        author="Active Author",
        isbn=isbn_1,
        status="CHECKED_OUT",
        publication_year=2020,
    )
    book_overdue = Book(
        title="Overdue Book",
        author="Overdue Author",
        isbn=isbn_2,
        status="CHECKED_OUT",
        publication_year=2019,
    )
    db.add_all([book_active, book_overdue])
    db.commit()
    db.refresh(book_active)
    db.refresh(book_overdue)

    # Loan 1: Active, due in 7 days (not overdue)
    loan_1 = Loan(
        book_id=book_active.id,
        user_id=user.id,
        borrowed_at=now - timedelta(days=2),
        due_date=now + timedelta(days=7),
        status="ACTIVE",
    )
    # Loan 2: Active, due 3 days ago (overdue)
    loan_2 = Loan(
        book_id=book_overdue.id,
        user_id=user.id,
        borrowed_at=now - timedelta(days=17),
        due_date=now - timedelta(days=3),
        status="ACTIVE",
    )
    db.add_all([loan_1, loan_2])
    db.commit()
    db.refresh(loan_1)
    db.refresh(loan_2)
    id_1, id_2 = loan_1.id, loan_2.id
    bid_1, bid_2 = book_active.id, book_overdue.id
    db.close()

    try:
        res = client.get(
            "/api/circulation/my-loans",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

        # Map by id
        loans_by_id = {item["id"]: item for item in data if item["id"] in (id_1, id_2)}
        assert id_1 in loans_by_id
        assert id_2 in loans_by_id

        # Check loan 1: not overdue, contains book metadata
        assert loans_by_id[id_1]["is_overdue"] is False
        assert loans_by_id[id_1]["book_title"] == "Future Due Book"
        assert loans_by_id[id_1]["book_author"] == "Active Author"

        # Check loan 2: is overdue
        assert loans_by_id[id_2]["is_overdue"] is True
        assert loans_by_id[id_2]["book_title"] == "Overdue Book"
        assert loans_by_id[id_2]["book_author"] == "Overdue Author"

        # Status filter check
        res_active = client.get(
            "/api/circulation/my-loans?status_filter=ACTIVE",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_active.status_code == 200
        active_ids = [item["id"] for item in res_active.json()]
        assert id_1 in active_ids
        assert id_2 in active_ids

        res_returned = client.get(
            "/api/circulation/my-loans?status_filter=RETURNED",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_returned.status_code == 200
        returned_ids = [item["id"] for item in res_returned.json()]
        assert id_1 not in returned_ids
        assert id_2 not in returned_ids
    finally:
        db = SessionLocal()
        db.query(Loan).filter(Loan.id.in_([id_1, id_2])).delete(
            synchronize_session=False
        )
        db.query(Book).filter(Book.id.in_([bid_1, bid_2])).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


def test_circulation_loans_route_registered():
    """Verify /api/circulation/loans route is registered in FastAPI app."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/circulation/loans" in openapi_paths
    assert "get" in openapi_paths["/api/circulation/loans"]


def test_all_active_loans_requires_librarian():
    """Verify GET /api/circulation/loans rejects patron with HTTP 403."""
    db = SessionLocal()
    patron_token, _ = create_demo_jwt(UserRole.PATRON, db=db)
    db.close()

    res = client.get(
        "/api/circulation/loans",
        headers={"Authorization": f"Bearer {patron_token}"},
    )
    assert res.status_code == 403


def test_all_active_loans_success_and_overdue_filter():
    """Verify librarian can retrieve all active loans with patron email and overdue filter."""
    db = SessionLocal()
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN, db=db)
    _, patron_user = create_demo_jwt(UserRole.PATRON, db=db)
    now = datetime.now(UTC)

    isbn_active = f"978{int(time.time() * 1000)}"[:13]
    isbn_overdue = f"979{int(time.time() * 1000)}"[:13]

    book_active = Book(
        title="Librarian Active Book",
        author="Active Writer",
        isbn=isbn_active,
        status="CHECKED_OUT",
        publication_year=2021,
    )
    book_overdue = Book(
        title="Librarian Overdue Book",
        author="Overdue Writer",
        isbn=isbn_overdue,
        status="CHECKED_OUT",
        publication_year=2020,
    )
    db.add_all([book_active, book_overdue])
    db.commit()
    db.refresh(book_active)
    db.refresh(book_overdue)

    # Active loan (future due date)
    loan_active = Loan(
        book_id=book_active.id,
        user_id=patron_user.id,
        borrowed_at=now - timedelta(days=1),
        due_date=now + timedelta(days=13),
        status="ACTIVE",
    )
    # Overdue loan (past due date)
    loan_overdue = Loan(
        book_id=book_overdue.id,
        user_id=patron_user.id,
        borrowed_at=now - timedelta(days=20),
        due_date=now - timedelta(days=6),
        status="ACTIVE",
    )
    db.add_all([loan_active, loan_overdue])
    db.commit()
    db.refresh(loan_active)
    db.refresh(loan_overdue)
    id_active, id_overdue = loan_active.id, loan_overdue.id
    bid_active, bid_overdue = book_active.id, book_overdue.id
    db.close()

    try:
        # 1. Fetch all active loans
        res = client.get(
            "/api/circulation/loans",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

        loans_by_id = {
            item["id"]: item
            for item in data
            if item["id"] in (id_active, id_overdue)
        }
        assert id_active in loans_by_id
        assert id_overdue in loans_by_id

        # Verify patron_email is exposed
        assert loans_by_id[id_active]["patron_email"] == patron_user.email
        assert loans_by_id[id_overdue]["patron_email"] == patron_user.email

        # Verify overdue flags
        assert loans_by_id[id_active]["is_overdue"] is False
        assert loans_by_id[id_overdue]["is_overdue"] is True

        # 2. Fetch with overdue_only=true
        res_overdue = client.get(
            "/api/circulation/loans?overdue_only=true",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res_overdue.status_code == 200
        overdue_ids = [item["id"] for item in res_overdue.json()]
        assert id_overdue in overdue_ids
        assert id_active not in overdue_ids
    finally:
        db = SessionLocal()
        db.query(Loan).filter(Loan.id.in_([id_active, id_overdue])).delete(
            synchronize_session=False
        )
        db.query(Book).filter(Book.id.in_([bid_active, bid_overdue])).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


def test_circulation_intake_route_registered():
    """Verify /api/circulation/intake route is registered in the FastAPI app."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/circulation/intake" in openapi_paths
    assert "get" in openapi_paths["/api/circulation/intake"]


def test_intake_queue_unauthenticated():
    """Verify unauthenticated request to /api/circulation/intake returns 401."""
    res = client.get("/api/circulation/intake")
    assert res.status_code == 401


def test_intake_queue_patron_forbidden():
    """Verify patron role cannot access the intake queue and receives 403."""
    patron_token, _ = create_demo_jwt(UserRole.PATRON)
    res = client.get(
        "/api/circulation/intake",
        headers={"Authorization": f"Bearer {patron_token}"},
    )
    assert res.status_code == 403


def test_intake_queue_librarian_filtering_and_fifo_ordering():
    """Verify librarian can fetch intake queue and receives only IN_PROCESSING books in FIFO order."""
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    db = SessionLocal()

    ts = int(time.time() * 1000)
    b_earlier = Book(
        title=f"Intake Book Earlier {ts}",
        author="Author A",
        isbn=f"9780{uuid.uuid4().hex[:9]}",
        status="IN_PROCESSING",
        publication_year=2020,
        updated_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    b_later = Book(
        title=f"Intake Book Later {ts}",
        author="Author B",
        isbn=f"9780{uuid.uuid4().hex[:9]}",
        status="IN_PROCESSING",
        publication_year=2021,
        updated_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    b_available = Book(
        title=f"Available Book {ts}",
        author="Author C",
        isbn=f"9780{uuid.uuid4().hex[:9]}",
        status="AVAILABLE",
        publication_year=2022,
    )
    db.add_all([b_earlier, b_later, b_available])
    db.commit()
    db.refresh(b_earlier)
    db.refresh(b_later)
    db.refresh(b_available)

    earlier_id = b_earlier.id
    later_id = b_later.id
    available_id = b_available.id
    db.close()

    try:
        res = client.get(
            "/api/circulation/intake",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res.status_code == 200
        items = res.json()
        assert isinstance(items, list)

        # Verify all items in the queue are in IN_PROCESSING status
        for item in items:
            assert item["status"] == "IN_PROCESSING"

        # Verify our available book is not in the intake queue
        item_ids = [item["id"] for item in items]
        assert available_id not in item_ids
        assert earlier_id in item_ids
        assert later_id in item_ids

        # Verify FIFO ordering: b_earlier must appear before b_later
        idx_earlier = item_ids.index(earlier_id)
        idx_later = item_ids.index(later_id)
        assert idx_earlier < idx_later
    finally:
        db = SessionLocal()
        db.query(Book).filter(Book.id.in_([earlier_id, later_id, available_id])).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


def test_circulation_shelve_route_registered():
    """Verify /api/circulation/shelve/{book_id} route is registered in the FastAPI app."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/circulation/shelve/{book_id}" in openapi_paths
    assert "post" in openapi_paths["/api/circulation/shelve/{book_id}"]


def test_shelve_unauthenticated():
    """Verify unauthenticated request to shelve endpoint returns 401."""
    res = client.post("/api/circulation/shelve/1")
    assert res.status_code == 401


def test_shelve_patron_forbidden():
    """Verify patron role cannot shelve books and receives 403."""
    patron_token, _ = create_demo_jwt(UserRole.PATRON)
    res = client.post(
        "/api/circulation/shelve/1",
        headers={"Authorization": f"Bearer {patron_token}"},
    )
    assert res.status_code == 403


def test_shelve_book_not_found():
    """Verify shelving nonexistent book returns 404."""
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    res = client.post(
        "/api/circulation/shelve/999999",
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Book #999999 not found"


def test_shelve_invalid_status_conflict():
    """Verify shelving a book that is not in IN_PROCESSING returns 400 Bad Request."""
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    db = SessionLocal()

    ts = int(time.time() * 1000)
    book = Book(
        title=f"Already Available {ts}",
        author="Author",
        isbn=f"9780{uuid.uuid4().hex[:9]}",
        status="AVAILABLE",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    try:
        res = client.post(
            f"/api/circulation/shelve/{book_id}",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res.status_code == 400
        assert "Cannot shelve book with status 'AVAILABLE'" in res.json()["detail"]
    finally:
        db = SessionLocal()
        db.query(Book).filter(Book.id == book_id).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_shelve_success_in_processing_to_available():
    """Verify successful shelve transitions book from IN_PROCESSING to AVAILABLE."""
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    db = SessionLocal()

    ts = int(time.time() * 1000)
    book = Book(
        title=f"Intake Book {ts}",
        author="Author",
        isbn=f"9780{uuid.uuid4().hex[:9]}",
        status="IN_PROCESSING",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    try:
        res = client.post(
            f"/api/circulation/shelve/{book_id}",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == book_id
        assert data["status"] == "AVAILABLE"

        # Verify database persisted state
        db = SessionLocal()
        refreshed = db.query(Book).filter(Book.id == book_id).first()
        assert refreshed.status == "AVAILABLE"
        db.close()
    finally:
        db = SessionLocal()
        db.query(Book).filter(Book.id == book_id).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_shelve_concurrent_race_condition():
    """Verify concurrent shelve requests on the same IN_PROCESSING book are serialized by row locking."""
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    db = SessionLocal()

    ts = int(time.time() * 1000)
    book = Book(
        title=f"Race Shelve Book {ts}",
        author="Author",
        isbn=f"9780{uuid.uuid4().hex[:9]}",
        status="IN_PROCESSING",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    def do_shelve():
        c = TestClient(app)
        return c.post(
            f"/api/circulation/shelve/{book_id}",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(do_shelve)
            future2 = executor.submit(do_shelve)
            res1 = future1.result()
            res2 = future2.result()

        status_codes = sorted([res1.status_code, res2.status_code])
        # Exactly one request must succeed (200), and the other must be rejected (400) because status changed
        assert status_codes == [200, 400]

        # Verify final database state is AVAILABLE
        db = SessionLocal()
        final_book = db.query(Book).filter(Book.id == book_id).first()
        assert final_book.status == "AVAILABLE"
        db.close()
    finally:
        db = SessionLocal()
        db.query(Book).filter(Book.id == book_id).delete(synchronize_session=False)
        db.commit()
        db.close()
