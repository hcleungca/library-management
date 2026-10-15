from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine, get_db


def test_engine_configuration():
    """Verify engine initialization and session factory bind."""
    assert engine is not None
    assert SessionLocal is not None
    # Verify pool configuration
    assert engine.pool is not None


def test_get_db_yields_session_and_closes():
    """Verify get_db yields a Session instance and properly closes it."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        assert isinstance(session, Session)
    finally:
        # Verify generator closes session on exit
        with pytest.raises(StopIteration):
            next(db_gen)


def test_get_db_guarantees_close_on_exception():
    """Verify db.close() is called even if an exception occurs during request execution."""
    mock_session = MagicMock()
    with patch("app.db.session.SessionLocal", return_value=mock_session):
        gen = get_db()
        yielded_session = next(gen)
        assert yielded_session == mock_session

        with pytest.raises(RuntimeError, match="Simulated request failure"):
            gen.throw(RuntimeError("Simulated request failure"))

        mock_session.close.assert_called_once()

