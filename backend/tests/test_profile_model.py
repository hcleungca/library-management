from app.models.profile import Profile


def test_profile_table_name():
    """Verify table name is profiles."""
    assert Profile.__tablename__ == "profiles"


def test_profile_columns():
    """Verify Profile columns exist and match specification."""
    columns = {c.name for c in Profile.__table__.columns}
    assert "id" in columns
    assert "email" in columns
    assert "full_name" in columns
    assert "role" in columns
    assert "created_at" in columns
    # Explicitly verify avatar_url was dropped per request
    assert "avatar_url" not in columns


def test_profile_column_constraints():
    """Verify constraints: id is PK, email is unique, role defaults to PATRON."""
    id_col = Profile.__table__.columns["id"]
    assert id_col.primary_key is True

    email_col = Profile.__table__.columns["email"]
    assert email_col.unique is True
    assert email_col.nullable is False

    role_col = Profile.__table__.columns["role"]
    assert role_col.default.arg == "PATRON"
    assert role_col.nullable is False
