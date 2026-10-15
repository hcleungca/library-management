import uuid

import pytest
from pydantic import ValidationError

from app.schemas.auth import TokenUser, UserRole


def test_user_role_values():
    """Verify UserRole enum values."""
    assert UserRole.PATRON == "PATRON"
    assert UserRole.LIBRARIAN == "LIBRARIAN"
    assert list(UserRole) == [UserRole.PATRON, UserRole.LIBRARIAN]


def test_token_user_valid_creation():
    """Verify TokenUser creation with valid fields and defaults."""
    user_id = uuid.uuid4()
    user = TokenUser(
        id=user_id,
        email="patron@example.com",
    )
    assert user.id == user_id
    assert user.email == "patron@example.com"
    assert user.role == UserRole.PATRON
    assert user.full_name is None


def test_token_user_explicit_fields():
    """Verify TokenUser with explicit role and name."""
    user_id = str(uuid.uuid4())
    user = TokenUser(
        id=user_id,
        email="librarian@example.com",
        role=UserRole.LIBRARIAN,
        full_name="Ada Lovelace",
    )
    assert str(user.id) == user_id
    assert user.role == UserRole.LIBRARIAN
    assert user.full_name == "Ada Lovelace"


def test_token_user_invalid_role():
    """Verify invalid role string raises ValidationError."""
    with pytest.raises(ValidationError):
        TokenUser(
            id=uuid.uuid4(),
            email="invalid@example.com",
            role="SUPERUSER",  # type: ignore[arg-type]
        )


def test_token_user_invalid_uuid():
    """Verify invalid UUID string raises ValidationError."""
    with pytest.raises(ValidationError):
        TokenUser(
            id="not-a-valid-uuid",  # type: ignore[arg-type]
            email="invalid@example.com",
        )


def test_token_user_from_attributes():
    """Verify TokenUser can be populated from object attributes (ORM compatibility)."""

    class MockProfile:
        def __init__(self):
            self.id = uuid.uuid4()
            self.email = "profile@example.com"
            self.role = "LIBRARIAN"
            self.full_name = "Library Staff"

    profile = MockProfile()
    token_user = TokenUser.model_validate(profile)

    assert token_user.id == profile.id
    assert token_user.email == profile.email
    assert token_user.role == UserRole.LIBRARIAN
    assert token_user.full_name == "Library Staff"


def test_token_user_omits_avatar_url():
    """Verify avatar_url is not present in TokenUser schema fields."""
    assert "avatar_url" not in TokenUser.model_fields


def test_demo_token_request_and_response_schemas():
    """Verify DemoTokenRequest defaults and TokenResponse payload structure."""
    from app.schemas.auth import DemoTokenRequest, TokenResponse

    req = DemoTokenRequest()
    assert req.role == UserRole.PATRON

    req_lib = DemoTokenRequest(role=UserRole.LIBRARIAN)
    assert req_lib.role == UserRole.LIBRARIAN

    user = TokenUser(
        id=uuid.uuid4(),
        email="demo@example.com",
        role=UserRole.PATRON,
    )
    res = TokenResponse(
        access_token="mock.jwt.token",
        token_type="bearer",
        user=user,
    )
    assert res.access_token == "mock.jwt.token"
    assert res.token_type == "bearer"
    assert res.user.email == "demo@example.com"
