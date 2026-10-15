from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

client = TestClient(app)


def test_health_check_healthy():
    """Verify health endpoint returns healthy and connected status when database is reachable."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_health_check_degraded_on_db_error():
    """Verify health endpoint handles database exception gracefully and reports degraded status."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = RuntimeError("Database connection timed out")

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert "unreachable: Database connection timed out" in data["database"]
        assert "timestamp" in data
    finally:
        app.dependency_overrides.clear()

