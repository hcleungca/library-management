from app.models.loan import Loan


def test_loan_table_name():
    """Verify table name is loans."""
    assert Loan.__tablename__ == "loans"


def test_loan_columns():
    """Verify all expected columns exist on the loans table."""
    columns = {c.name for c in Loan.__table__.columns}
    expected = {
        "id",
        "book_id",
        "user_id",
        "borrowed_at",
        "due_date",
        "returned_at",
        "status",
    }
    assert expected == columns


def test_loan_column_constraints():
    """Verify column constraints, foreign keys, and defaults."""
    table = Loan.__table__

    assert table.columns["id"].primary_key is True

    # Foreign key on book_id
    book_fk = next(iter(table.columns["book_id"].foreign_keys))
    assert book_fk.target_fullname == "books.id"
    assert book_fk.ondelete == "CASCADE"
    assert table.columns["book_id"].nullable is False

    # Foreign key on user_id
    user_fk = next(iter(table.columns["user_id"].foreign_keys))
    assert user_fk.target_fullname == "profiles.id"
    assert user_fk.ondelete == "CASCADE"
    assert table.columns["user_id"].nullable is False

    # Date constraints
    assert table.columns["due_date"].nullable is False
    assert table.columns["returned_at"].nullable is True

    # Status defaults
    assert table.columns["status"].default.arg == "ACTIVE"
    assert table.columns["status"].nullable is False

