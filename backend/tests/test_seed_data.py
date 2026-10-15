from collections import Counter

from scripts.seed_data import SEED_BOOKS


def test_seed_books_count_and_status_distribution():
    """Verify exactly 15 books with required lifecycle distribution."""
    assert len(SEED_BOOKS) == 15
    counts = Counter(b["status"] for b in SEED_BOOKS)
    assert counts["AVAILABLE"] == 6
    assert counts["CHECKED_OUT"] == 4
    assert counts["IN_PROCESSING"] == 3
    assert counts["IN_MAINTENANCE"] == 2


def test_seed_books_fields_complete():
    """Verify all books have complete, non-empty metadata fields."""
    required_fields = {
        "title",
        "author",
        "isbn",
        "genre",
        "publication_year",
        "dewey_decimal",
        "summary",
        "cover_image_url",
        "status",
    }
    for b in SEED_BOOKS:
        for f in required_fields:
            assert f in b, f"Missing field {f} in {b.get('title')}"
            assert b[f] is not None, f"Field {f} is None in {b.get('title')}"
        assert "total_copies" not in b


def test_seed_books_unique_isbns():
    """Verify all 15 books have unique ISBN identifiers."""
    isbns = [b["isbn"] for b in SEED_BOOKS]
    assert len(isbns) == len(set(isbns))


def test_seed_books_overdue_and_maintenance_helpers():
    """Verify overdue loan item and damage notes exist."""
    overdue_books = [b for b in SEED_BOOKS if b.get("is_overdue") is True]
    assert len(overdue_books) == 1
    assert overdue_books[0]["status"] == "CHECKED_OUT"

    maintenance_books = [b for b in SEED_BOOKS if b["status"] == "IN_MAINTENANCE"]
    assert len(maintenance_books) == 2
    for mb in maintenance_books:
        assert "initial_damage_note" in mb
        assert len(mb["initial_damage_note"]) > 10
