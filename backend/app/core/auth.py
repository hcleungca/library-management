"""Authentication and Role-Based Access Control (RBAC) dependencies.

Handles Supabase JWT validation, user profile lookup, role enforcement,
and non-production demo role switcher fallbacks.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Profile
from app.schemas.auth import TokenUser, UserRole

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

DEMO_PATRON_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_LIBRARIAN_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _get_demo_user(role: UserRole, db: Session | None = None) -> TokenUser:
    """Retrieve demo profile from database or return default mock demo user."""
    email = (
        "librarian@example.com"
        if role == UserRole.LIBRARIAN
        else "patron@example.com"
    )
    if db is not None:
        try:
            profile = db.query(Profile).filter(Profile.email == email).first()
            if profile:
                return TokenUser.model_validate(profile)
        except SQLAlchemyError as exc:
            logger.debug("DB profile lookup failed in demo fallback: %s", exc)

    return TokenUser(
        id=DEMO_LIBRARIAN_ID if role == UserRole.LIBRARIAN else DEMO_PATRON_ID,
        email=email,
        role=role,
        full_name=(
            "Demo Librarian" if role == UserRole.LIBRARIAN else "Demo Patron"
        ),
    )


def create_demo_jwt(
    role: UserRole, db: Session | None = None
) -> tuple[str, TokenUser]:
    """Generate an authentic signed JWT bearer token for the specified demo user role."""
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured",
        )

    demo_user = _get_demo_user(role, db=db)
    now = datetime.now(UTC)
    payload = {
        "sub": str(demo_user.id),
        "email": demo_user.email,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "user_metadata": {
            "role": demo_user.role.value,
            "full_name": demo_user.full_name,
        },
        "app_metadata": {
            "provider": "demo",
            "role": demo_user.role.value,
        },
    }
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return token, demo_user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> TokenUser:
    """Extract and validate authenticated user from Supabase JWT.

    1. Checks for Authorization header bearer token.
    2. Decodes JWT using HS256 with settings.SUPABASE_JWT_SECRET,
       extracts sub (UUID) and email, and queries the user's Profile from the DB.
    3. Dev Mode Fallback: When DEBUG=True and no token is passed,
       falls back to demo patron for convenience.
    4. Raises HTTP 401 Unauthorized if credentials cannot be validated.
    """
    # If Bearer token is provided, validate it
    if credentials is not None and credentials.credentials:
        token = credentials.credentials
        if not settings.SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_JWT_SECRET is not configured",
            )
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id = uuid.UUID(sub)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = payload.get("email") or ""

        # Fetch corresponding Profile from DB for up-to-date role
        try:
            profile = db.query(Profile).filter(Profile.id == user_id).first()
            if profile:
                return TokenUser.model_validate(profile)
        except SQLAlchemyError as exc:
            logger.debug(
                "DB profile lookup failed during JWT verification: %s", exc
            )

        # Fallback to claims in token if profile not found in DB
        user_meta = payload.get("user_metadata", {})
        app_meta = payload.get("app_metadata", {})
        claim_role = (
            user_meta.get("role")
            or app_meta.get("role")
            or payload.get("role")
            or "PATRON"
        )
        try:
            role = UserRole(str(claim_role).upper())
        except ValueError:
            role = UserRole.PATRON

        full_name = user_meta.get("full_name") or payload.get("full_name")

        return TokenUser(
            id=user_id,
            email=email,
            role=role,
            full_name=full_name,
        )

    # Dev / Demo Mode Fallback when no token is passed
    if settings.DEBUG:
        return _get_demo_user(UserRole.PATRON, db=db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: UserRole | str):
    """Enforce role-based access control (RBAC).

    LIBRARIAN role inherits all PATRON capabilities.
    """
    target_role = (
        UserRole(required_role)
        if isinstance(required_role, str)
        else required_role
    )

    def role_checker(
        current_user: TokenUser = Depends(get_current_user),
    ) -> TokenUser:
        if (
            current_user.role != target_role
            and current_user.role != UserRole.LIBRARIAN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )
        return current_user

    return role_checker
