from app.models.maintenance import MaintenanceLog


def test_maintenance_log_table_name():
    """Verify table name is maintenance_logs."""
    assert MaintenanceLog.__tablename__ == "maintenance_logs"


def test_maintenance_log_columns():
    """Verify all expected columns exist on the maintenance_logs table."""
    columns = {c.name for c in MaintenanceLog.__table__.columns}
    expected = {
        "id",
        "book_id",
        "logged_by",
        "damage_description",
        "severity",
        "recommended_action",
        "resolved_at",
        "created_at",
    }
    assert expected == columns


def test_maintenance_log_column_constraints():
    """Verify column constraints, foreign keys, and defaults."""
    table = MaintenanceLog.__table__

    assert table.columns["id"].primary_key is True

    # Foreign key on book_id with CASCADE
    book_fk = next(iter(table.columns["book_id"].foreign_keys))
    assert book_fk.target_fullname == "books.id"
    assert book_fk.ondelete == "CASCADE"
    assert table.columns["book_id"].nullable is False

    # Foreign key on logged_by (no cascade delete to preserve audit history)
    logged_by_fk = next(iter(table.columns["logged_by"].foreign_keys))
    assert logged_by_fk.target_fullname == "profiles.id"
    assert logged_by_fk.ondelete is None
    assert table.columns["logged_by"].nullable is False

    # Content & Severity
    assert table.columns["damage_description"].nullable is False
    assert table.columns["severity"].default.arg == "MODERATE"
    assert table.columns["severity"].nullable is False

    # Resolution fields
    assert table.columns["recommended_action"].nullable is True
    assert table.columns["resolved_at"].nullable is True

