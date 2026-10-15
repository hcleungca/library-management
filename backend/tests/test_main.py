from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns 200 and running message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Intelligent Library API is running"}


def test_cors_headers_applied():
    """Verify CORS headers are returned for allowed origins."""
    origin = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:5173"
    response = client.get("/", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_docs_endpoints_accessible():
    """Verify Swagger UI and OpenAPI documentation schema are served."""
    docs_res = client.get("/docs")
    assert docs_res.status_code == 200

    openapi_res = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()
    assert schema["info"]["title"] == settings.PROJECT_NAME

