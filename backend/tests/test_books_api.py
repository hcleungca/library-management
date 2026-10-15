from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_books_route_registered():
    """Verify /api/books route is registered in the FastAPI app."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/books" in openapi_paths
    assert "get" in openapi_paths["/api/books"]


def test_list_books_success():
    """Verify GET /api/books returns 200 with items array and total count."""
    response = client.get("/api/books")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert data["total"] >= 15


def test_list_books_status_filter():
    """Verify filtering by book status."""
    for status in ("AVAILABLE", "CHECKED_OUT", "IN_PROCESSING"):
        response = client.get(f"/api/books?status={status}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert item["status"] == status


def test_list_books_genre_filter():
    """Verify filtering by genre case-insensitively."""
    response = client.get("/api/books?genre=distributed")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert "distributed" in item["genre"].lower()


def test_list_books_search_by_title_and_author():
    """Verify text search matches across title and author case-insensitively."""
    # Search by title keyword
    res_title = client.get("/api/books?search=refactoring")
    assert res_title.status_code == 200
    data_title = res_title.json()
    assert data_title["total"] >= 1
    assert any("refactoring" in b["title"].lower() for b in data_title["items"])

    # Search by author keyword
    res_author = client.get("/api/books?search=martin")
    assert res_author.status_code == 200
    data_author = res_author.json()
    assert data_author["total"] >= 1
    assert any("martin" in b["author"].lower() for b in data_author["items"])

    # Search by summary keyword
    res_summary = client.get("/api/books?search=consensus")
    assert res_summary.status_code == 200
    data_summary = res_summary.json()
    assert data_summary["total"] >= 1
    assert any("consensus" in (b["summary"] or "").lower() for b in data_summary["items"])


def test_list_books_pagination():
    """Verify skip and limit parameters control pagination."""
    res_limit = client.get("/api/books?limit=5")
    assert res_limit.status_code == 200
    data_limit = res_limit.json()
    assert len(data_limit["items"]) == 5

    res_skip = client.get("/api/books?skip=5&limit=5")
    assert res_skip.status_code == 200
    data_skip = res_skip.json()
    assert len(data_skip["items"]) == 5

    # Ensure pages contain different items
    limit_ids = [b["id"] for b in data_limit["items"]]
    skip_ids = [b["id"] for b in data_skip["items"]]
    assert set(limit_ids).isdisjoint(set(skip_ids))


def test_list_books_no_results():
    """Verify search yielding no matches returns total 0 and empty items list."""
    response = client.get("/api/books?search=NonExistentBookXYZ123")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_get_book_detail_success():
    """Verify GET /api/books/{book_id} returns 200 with comprehensive book metadata."""
    # First get an existing book id from the catalog
    list_res = client.get("/api/books?limit=1")
    assert list_res.status_code == 200
    book_id = list_res.json()["items"][0]["id"]
    expected_title = list_res.json()["items"][0]["title"]

    detail_res = client.get(f"/api/books/{book_id}")
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["id"] == book_id
    assert data["title"] == expected_title
    assert "author" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_book_detail_not_found():
    """Verify GET /api/books/{book_id} returns 404 when ID does not exist."""
    response = client.get("/api/books/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book #999999 not found"


def test_get_book_detail_invalid_id():
    """Verify GET /api/books/{invalid_id} returns 422 for non-integer ID."""
    response = client.get("/api/books/invalid-id")
    assert response.status_code == 422


def test_create_book_requires_librarian_role():
    """Verify POST /api/books rejects patron requests with HTTP 403."""
    from app.core.auth import create_demo_jwt
    from app.schemas.auth import UserRole

    patron_token, _ = create_demo_jwt(UserRole.PATRON)
    payload = {
        "title": "Unauthorized Book",
        "author": "Hacker",
        "isbn": "9780000000001",
    }
    res = client.post(
        "/api/books",
        json=payload,
        headers={"Authorization": f"Bearer {patron_token}"},
    )
    assert res.status_code == 403


def test_create_book_success_and_duplicate_isbn():
    """Verify librarian can create a book and duplicate ISBN is rejected with HTTP 400."""
    import time

    from app.core.auth import create_demo_jwt
    from app.db.session import SessionLocal
    from app.models.book import Book
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    unique_isbn = f"978{int(time.time() * 1000)}"[:13]
    payload = {
        "title": "Test Driven Development",
        "author": "Kent Beck",
        "isbn": unique_isbn,
        "genre": "Software Engineering",
        "publication_year": 2002,
        "dewey_decimal": "005.1",
        "summary": "By example guide to TDD.",
        "status": "AVAILABLE",
    }

    created_id = None
    try:
        # 1. Create successfully
        res = client.post(
            "/api/books",
            json=payload,
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Test Driven Development"
        assert data["isbn"] == unique_isbn
        assert data["status"] == "AVAILABLE"
        created_id = data["id"]

        # 2. Duplicate ISBN returns HTTP 400
        res_dup = client.post(
            "/api/books",
            json=payload,
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res_dup.status_code == 400
        assert f"Book with ISBN '{unique_isbn}' already exists" in res_dup.json()["detail"]
    finally:
        if created_id is not None:
            db = SessionLocal()
            try:
                db.query(Book).filter(Book.id == created_id).delete()
                db.commit()
            finally:
                db.close()


def test_create_book_invalid_payload():
    """Verify missing required fields returns HTTP 422."""
    from app.core.auth import create_demo_jwt
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    res = client.post(
        "/api/books",
        json={"isbn": "12345"},
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert res.status_code == 422


def test_update_book_requires_librarian_role():
    """Verify PATCH /api/books/{book_id} rejects patron with HTTP 403."""
    from app.core.auth import create_demo_jwt
    from app.schemas.auth import UserRole

    patron_token, _ = create_demo_jwt(UserRole.PATRON)
    res = client.patch(
        "/api/books/1",
        json={"summary": "New summary"},
        headers={"Authorization": f"Bearer {patron_token}"},
    )
    assert res.status_code == 403


def test_update_book_not_found():
    """Verify PATCH /api/books/999999 returns HTTP 404."""
    from app.core.auth import create_demo_jwt
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    res = client.patch(
        "/api/books/999999",
        json={"summary": "New summary"},
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Book #999999 not found"


def test_update_book_partial_update_and_isbn_uniqueness():
    """Verify partial updates preserve existing fields and enforce ISBN uniqueness."""
    import time

    from app.core.auth import create_demo_jwt
    from app.db.session import SessionLocal
    from app.models.book import Book
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)

    isbn_a = f"978{int(time.time() * 1000)}"[:13]
    isbn_b = f"979{int(time.time() * 1000)}"[:13]

    db = SessionLocal()
    book_a = Book(
        title="Book A",
        author="Author A",
        isbn=isbn_a,
        status="AVAILABLE",
        publication_year=2020,
    )
    book_b = Book(
        title="Book B",
        author="Author B",
        isbn=isbn_b,
        status="AVAILABLE",
        publication_year=2021,
    )
    db.add_all([book_a, book_b])
    db.commit()
    db.refresh(book_a)
    db.refresh(book_b)
    id_a, id_b = book_a.id, book_b.id
    db.close()

    try:
        # 1. Partial update Book A summary and year only; title & author must remain unchanged
        patch_res = client.patch(
            f"/api/books/{id_a}",
            json={"summary": "Updated summary text", "publication_year": 2024},
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert patch_res.status_code == 200
        data = patch_res.json()
        assert data["title"] == "Book A"
        assert data["author"] == "Author A"
        assert data["isbn"] == isbn_a
        assert data["summary"] == "Updated summary text"
        assert data["publication_year"] == 2024

        # 2. Update Book A with its own ISBN should succeed
        self_isbn_res = client.patch(
            f"/api/books/{id_a}",
            json={"isbn": isbn_a},
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert self_isbn_res.status_code == 200

        # 3. Update Book A with Book B's ISBN should fail with HTTP 400
        dup_res = client.patch(
            f"/api/books/{id_a}",
            json={"isbn": isbn_b},
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert dup_res.status_code == 400
        assert f"ISBN '{isbn_b}' already in use" in dup_res.json()["detail"]
    finally:
        db = SessionLocal()
        db.query(Book).filter(Book.id.in_([id_a, id_b])).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


def test_delete_book_requires_librarian_role():
    """Verify DELETE /api/books/{book_id} rejects patron with HTTP 403."""
    from app.core.auth import create_demo_jwt
    from app.schemas.auth import UserRole

    patron_token, _ = create_demo_jwt(UserRole.PATRON)
    res = client.delete(
        "/api/books/1",
        headers={"Authorization": f"Bearer {patron_token}"},
    )
    assert res.status_code == 403


def test_delete_book_not_found():
    """Verify DELETE /api/books/999999 returns HTTP 404."""
    from app.core.auth import create_demo_jwt
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    res = client.delete(
        "/api/books/999999",
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Book #999999 not found"


def test_delete_book_checked_out_blocked():
    """Verify DELETE /api/books/{book_id} returns HTTP 400 when book is CHECKED_OUT."""
    import time

    from app.core.auth import create_demo_jwt
    from app.db.session import SessionLocal
    from app.models.book import Book
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    db = SessionLocal()
    book = Book(
        title="Active Loan Book",
        author="Author",
        isbn=isbn,
        status="CHECKED_OUT",
        publication_year=2021,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    book_id = book.id
    db.close()

    try:
        res = client.delete(
            f"/api/books/{book_id}",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert res.status_code == 400
        assert (
            res.json()["detail"]
            == "Cannot delete book that is currently checked out by a patron"
        )
    finally:
        db = SessionLocal()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


def test_delete_book_success():
    """Verify DELETE /api/books/{book_id} hard-deletes a book with no loan history and frees ISBN."""
    import time

    from app.core.auth import create_demo_jwt
    from app.db.session import SessionLocal
    from app.models.book import Book
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    db = SessionLocal()
    book = Book(
        title="Disposable Book",
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

    # Delete book
    res = client.delete(
        f"/api/books/{book_id}",
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert res.status_code == 204

    # Verify book is completely removed from DB (hard deleted)
    db = SessionLocal()
    deleted_row = db.query(Book).filter(Book.id == book_id).first()
    db.close()
    assert deleted_row is None

    # Verify ISBN is freed up for a new book
    recreate_res = client.post(
        "/api/books",
        json={
            "title": "Recreated Book with Same ISBN",
            "author": "New Author",
            "isbn": isbn,
        },
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert recreate_res.status_code == 201
    new_id = recreate_res.json()["id"]

    # Cleanup
    db = SessionLocal()
    db.query(Book).filter(Book.id == new_id).delete()
    db.commit()
    db.close()


def test_delete_book_with_past_history_soft_deletes():
    """Verify deleting a book with past loan history soft-deletes it and frees ISBN."""
    import time
    import uuid
    from datetime import UTC, datetime, timedelta

    from app.core.auth import create_demo_jwt
    from app.db.session import SessionLocal
    from app.models.book import Book
    from app.models.loan import Loan
    from app.models.profile import Profile
    from app.schemas.auth import UserRole

    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)
    patron_token, patron_user = create_demo_jwt(UserRole.PATRON)
    isbn = f"978{int(time.time() * 1000)}"[:13]

    db = SessionLocal()
    # Ensure profile exists in DB
    profile = db.query(Profile).filter(Profile.id == patron_user.id).first()
    if not profile:
        profile = Profile(
            id=patron_user.id,
            email=patron_user.email,
            role="PATRON",
            full_name=patron_user.full_name,
        )
        db.add(profile)
        db.flush()

    # Create book
    book = Book(
        title="Historical Book",
        author="Historical Author",
        isbn=isbn,
        status="AVAILABLE",
        publication_year=2020,
    )
    db.add(book)
    db.flush()
    book_id = book.id

    # Create a completed (RETURNED) past loan
    past_loan = Loan(
        book_id=book_id,
        user_id=patron_user.id,
        borrowed_at=datetime.now(UTC) - timedelta(days=20),
        due_date=datetime.now(UTC) - timedelta(days=6),
        returned_at=datetime.now(UTC) - timedelta(days=5),
        status="RETURNED",
    )
    db.add(past_loan)
    db.commit()
    loan_id = past_loan.id
    db.close()

    try:
        # Delete book via API
        del_res = client.delete(
            f"/api/books/{book_id}",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert del_res.status_code == 204

        # Catalog and single GET should now return 404
        get_res = client.get(f"/api/books/{book_id}")
        assert get_res.status_code == 404

        # Verify book row still exists in DB as DECOMMISSIONED with ISBN freed
        db = SessionLocal()
        book_row = db.query(Book).filter(Book.id == book_id).first()
        assert book_row is not None
        assert book_row.status == "DECOMMISSIONED"
        assert book_row.isbn is None
        assert f"Former ISBN: {isbn}" in book_row.summary
        db.close()

        # Verify patron's past loan history still renders without 500
        my_loans_res = client.get(
            "/api/circulation/my-loans",
            headers={"Authorization": f"Bearer {patron_token}"},
        )
        assert my_loans_res.status_code == 200
        loans_data = my_loans_res.json()
        matching_loan = next((l for l in loans_data if l["id"] == loan_id), None)
        assert matching_loan is not None
        assert matching_loan["book_title"] == "Historical Book"

        # Verify the freed ISBN can now be cataloged by a new book
        new_book_res = client.post(
            "/api/books",
            json={
                "title": "Brand New Edition",
                "author": "New Author",
                "isbn": isbn,
            },
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert new_book_res.status_code == 201
        new_book_id = new_book_res.json()["id"]

        # Cleanup new book
        db = SessionLocal()
        db.query(Book).filter(Book.id == new_book_id).delete()
        db.commit()
        db.close()
    finally:
        # Cleanup historical loan and book
        db = SessionLocal()
        db.query(Loan).filter(Loan.id == loan_id).delete()
        db.query(Book).filter(Book.id == book_id).delete()
        db.commit()
        db.close()


