from unittest.mock import MagicMock, patch

import pytest

from app.models import Profile
from scripts.seed import get_or_create_profile, seed_database


def test_get_or_create_profile_existing():
    """Verify get_or_create_profile returns existing profile when found."""
    mock_db = MagicMock()
    existing_profile = Profile(
        email="existing@example.com",
        full_name="Existing User",
        role="PATRON",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing_profile

    result = get_or_create_profile(
        mock_db,
        email="existing@example.com",
        full_name="Existing User",
        role="PATRON",
    )

    assert result == existing_profile
    mock_db.add.assert_not_called()


def test_get_or_create_profile_new():
    """Verify get_or_create_profile creates and flushes new profile when not found."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = get_or_create_profile(
        mock_db,
        email="new@example.com",
        full_name="New User",
        role="LIBRARIAN",
    )

    assert result.email == "new@example.com"
    assert result.full_name == "New User"
    assert result.role == "LIBRARIAN"
    mock_db.add.assert_called_once_with(result)
    mock_db.flush.assert_called_once()


def test_seed_database_idempotent_execution():
    """Verify seed_database executes successfully and returns expected summary counts."""
    summary = seed_database()
    assert summary == {
        "profiles": 2,
        "books": 15,
        "loans": 4,
        "maintenance_logs": 2,
    }


def test_seed_database_rollback_on_exception():
    """Verify seed_database rolls back and closes session on unexpected database error."""
    mock_db = MagicMock()
    mock_db.query.side_effect = RuntimeError("Database connection failure")

    with patch("scripts.seed.SessionLocal", return_value=mock_db):
        with pytest.raises(RuntimeError, match="Database connection failure"):
            seed_database()

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()
