import uuid
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.core.auth import get_current_user, require_role
from app.core.config import settings
from app.schemas.auth import TokenUser, UserRole


def test_require_role_allows_matching_role():
    """Verify require_role allows user with exact required role."""
    checker = require_role(UserRole.LIBRARIAN)
    user = TokenUser(
        id=uuid.uuid4(),
        email="librarian@example.com",
        role=UserRole.LIBRARIAN,
    )
    result = checker(current_user=user)
    assert result == user


def test_require_role_blocks_insufficient_role():
    """Verify require_role rejects patron attempting librarian action with HTTP 403."""
    checker = require_role(UserRole.LIBRARIAN)
    patron_user = TokenUser(
        id=uuid.uuid4(),
        email="patron@example.com",
        role=UserRole.PATRON,
    )
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=patron_user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient role permissions"


def test_require_role_librarian_inherits_patron():
    """Verify librarian inherits patron permissions when patron role is required."""
    checker = require_role(UserRole.PATRON)
    librarian_user = TokenUser(
        id=uuid.uuid4(),
        email="librarian@example.com",
        role=UserRole.LIBRARIAN,
    )
    result = checker(current_user=librarian_user)
    assert result == librarian_user


def test_get_current_user_dev_mode_default_patron(monkeypatch):
    """Verify get_current_user returns demo patron in dev mode with no token."""
    monkeypatch.setattr(settings, "DEBUG", True)
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    user = get_current_user(credentials=None, db=mock_db)
    assert user.role == UserRole.PATRON
    assert user.email == "patron@example.com"


def test_get_current_user_production_missing_token_raises_401(monkeypatch):
    """Verify missing credentials in production mode raises HTTP 401."""
    monkeypatch.setattr(settings, "DEBUG", False)
    mock_db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=mock_db)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_valid_jwt(monkeypatch):
    """Verify valid Supabase JWT token decoding and user extraction."""
    jwt_secret = "test-secret-key-12345678901234567890"
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", jwt_secret)

    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "email": "user@example.com",
        "user_metadata": {
            "role": "PATRON",
            "full_name": "Test Patron",
        },
    }
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    user = get_current_user(credentials=credentials, db=mock_db)
    assert str(user.id) == user_id
    assert user.email == "user@example.com"
    assert user.role == UserRole.PATRON
    assert user.full_name == "Test Patron"


def test_get_current_user_invalid_jwt_raises_401(monkeypatch):
    """Verify malformed or invalid signature JWT raises HTTP 401."""
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "correct-secret")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid.token.payload"
    )
    mock_db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=mock_db)
    assert exc_info.value.status_code == 401


def test_fastapi_endpoint_rbac_integration(monkeypatch):
    """Verify require_role dependency works seamlessly in a FastAPI router with Bearer auth."""
    from app.core.auth import create_demo_jwt

    app = FastAPI()
    librarian_guard = require_role(UserRole.LIBRARIAN)

    @app.get("/librarian-only")
    def librarian_route(user: TokenUser = Depends(librarian_guard)):
        return {"user": user.email, "role": user.role}

    client = TestClient(app)

    patron_token, _ = create_demo_jwt(UserRole.PATRON)
    librarian_token, _ = create_demo_jwt(UserRole.LIBRARIAN)

    # 1. With Patron Bearer Token -> 403 Forbidden
    res_patron = client.get(
        "/librarian-only",
        headers={"Authorization": f"Bearer {patron_token}"},
    )
    assert res_patron.status_code == 403

    # 2. With Librarian Bearer Token -> 200 OK
    res_librarian = client.get(
        "/librarian-only",
        headers={"Authorization": f"Bearer {librarian_token}"},
    )
    assert res_librarian.status_code == 200
    assert res_librarian.json()["role"] == "LIBRARIAN"


def test_create_demo_jwt_and_bearer_auth_in_production(monkeypatch):
    """Verify demo token issuance works and satisfies Bearer auth even in production (DEBUG=False)."""
    from app.core.auth import create_demo_jwt
    from app.main import app

    monkeypatch.setattr(settings, "DEBUG", False)
    client = TestClient(app)

    # 1. Obtain demo token for patron
    token_patron, patron_user = create_demo_jwt(UserRole.PATRON)
    assert token_patron is not None
    assert patron_user.role == UserRole.PATRON

    # 2. Call demo-token endpoint via HTTP
    res_demo = client.post("/api/auth/demo-token", json={"role": "LIBRARIAN"})
    assert res_demo.status_code == 200
    data = res_demo.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "LIBRARIAN"

    librarian_token = data["access_token"]

    # 3. Use genuine JWT in Authorization header against a protected endpoint in DEBUG=False
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=librarian_token
    )
    user = get_current_user(credentials=credentials, db=mock_db)
    assert user.role == UserRole.LIBRARIAN
    assert user.email == "librarian@example.com"


def test_missing_supabase_jwt_secret_raises_500(monkeypatch):
    """Verify demo token generation falls back to dev key and get_current_user requires URL or secret."""
    from app.core.auth import create_demo_jwt

    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    mock_db = MagicMock()

    # Demo JWT generation succeeds with dev fallback key
    token, user = create_demo_jwt(UserRole.PATRON)
    assert token is not None
    assert user.role == UserRole.PATRON

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="any.token.here")
    with pytest.raises(HTTPException) as exc_validate:
        get_current_user(credentials=credentials, db=mock_db)
    assert exc_validate.value.status_code == 500
    assert "Neither SUPABASE_URL nor SUPABASE_JWT_SECRET is configured" in exc_validate.value.detail


def test_create_sso_jwt_and_endpoint():
    """Verify POST /api/auth/sso-token returns valid JWT with Alex Rivera SSO patron profile."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/auth/sso-token")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alex.rivera@gmail.com"
    assert "Alex Rivera" in data["user"]["full_name"]
    assert data["user"]["role"] == "PATRON"


def test_get_auth_config_endpoint():
    """Verify GET /api/auth/config returns Supabase public configuration."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/auth/config")
    assert response.status_code == 200
    data = response.json()
    assert "supabase_url" in data
    assert "supabase_anon_key" in data


def test_get_current_user_remote_verification_fallback(monkeypatch):
    """Verify get_current_user falls back to Supabase remote auth when local JWT signature mismatch."""
    from unittest.mock import patch, MagicMock
    from app.core.auth import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials

    remote_user_id = str(uuid.uuid4())
    remote_data = {
        "sub": remote_user_id,
        "email": "remote.user@gmail.com",
        "user_metadata": {"full_name": "Remote User", "role": "PATRON"},
        "app_metadata": {"provider": "google"},
    }

    with patch("app.core.auth._verify_supabase_token_remote", return_value=remote_data):
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="mismatched.jwt.token"
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user = get_current_user(credentials=credentials, db=mock_db)
        assert str(user.id) == remote_user_id
        assert user.email == "remote.user@gmail.com"
        assert user.full_name == "Remote User"
        assert user.role == UserRole.PATRON


