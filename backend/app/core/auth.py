"""Authentication and Role-Based Access Control (RBAC) dependencies.

Handles Supabase JWT validation, user profile lookup, role enforcement,
and non-production demo role switcher fallbacks.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

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


def _verify_supabase_token_remote(token: str) -> dict[str, Any] | None:
    """Verify Supabase JWT token directly against the Supabase Auth GoTrue service."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None
    try:
        import httpx

        url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": settings.SUPABASE_KEY,
        }
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                user_data = resp.json()
                return {
                    "sub": user_data.get("id"),
                    "email": user_data.get("email"),
                    "user_metadata": user_data.get("user_metadata", {}),
                    "app_metadata": user_data.get("app_metadata", {}),
                }
            logger.debug(
                "Supabase remote auth responded with status %d: %s",
                resp.status_code,
                resp.text,
            )
    except Exception as exc:
        logger.warning("Remote Supabase token verification failed: %s", exc)
        
_jwks_client: Any = None


def _get_jwks_client() -> Any:
    """Retrieve or initialize cached PyJWKClient for asymmetric Supabase tokens."""
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_URL:
        try:
            from jwt import PyJWKClient

            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            _jwks_client = PyJWKClient(jwks_url, cache_keys=True, max_cached_keys=16)
        except Exception as exc:
            logger.debug("Failed to initialize PyJWKClient: %s", exc)
    return _jwks_client


def _get_or_create_user(
    email: str,
    full_name: str,
    role: UserRole,
    db: Session | None = None,
) -> TokenUser:
    """Retrieve profile from database or provision it dynamically with a real UUID."""
    if db is not None:
        try:
            profile = db.query(Profile).filter(Profile.email == email).first()
            if not profile:
                profile = Profile(
                    id=uuid.uuid4(),
                    email=email,
                    full_name=full_name,
                    role=role.value,
                )
                db.add(profile)
                db.commit()
                db.refresh(profile)
            return TokenUser.model_validate(profile)
        except SQLAlchemyError as exc:
            logger.debug("DB profile lookup failed, rolling back: %s", exc)
            db.rollback()

    try:
        from app.db.session import SessionLocal

        with SessionLocal() as session:
            profile = session.query(Profile).filter(Profile.email == email).first()
            if not profile:
                profile = Profile(
                    id=uuid.uuid4(),
                    email=email,
                    full_name=full_name,
                    role=role.value,
                )
                session.add(profile)
                session.commit()
                session.refresh(profile)
            return TokenUser.model_validate(profile)
    except Exception as exc:
        logger.debug("SessionLocal fallback failed: %s", exc)

    return TokenUser(
        id=uuid.uuid4(),
        email=email,
        role=role,
        full_name=full_name,
    )


DEV_FALLBACK_JWT_SECRET = "dev-demo-jwt-secret-key-for-local-development-only-12345"


def _get_signing_secret() -> str:
    """Return configured secret or fallback dev key for demo token issuance."""
    return settings.SUPABASE_JWT_SECRET or settings.SUPABASE_KEY or DEV_FALLBACK_JWT_SECRET


def create_demo_jwt(
    role: UserRole, db: Session | None = None
) -> tuple[str, TokenUser]:
    """Generate an authentic signed JWT bearer token for the specified demo user role."""
    secret = _get_signing_secret()

    email = (
        "librarian@example.com"
        if role == UserRole.LIBRARIAN
        else "patron@example.com"
    )
    full_name = "Demo Librarian" if role == UserRole.LIBRARIAN else "Demo Patron"
    demo_user = _get_or_create_user(
        email=email, full_name=full_name, role=role, db=db
    )
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
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, demo_user


def create_sso_jwt(
    email: str = "alex.rivera@gmail.com",
    full_name: str = "Alex Rivera (SSO)",
    db: Session | None = None,
) -> tuple[str, TokenUser]:
    """Generate a signed JWT token simulating Google / SSO library patron login."""
    secret = _get_signing_secret()

    user = _get_or_create_user(
        email=email, full_name=full_name, role=UserRole.PATRON, db=db
    )
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "user_metadata": {
            "role": user.role.value,
            "full_name": user.full_name,
        },
        "app_metadata": {
            "provider": "google_sso",
            "role": user.role.value,
        },
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, user


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
        if not settings.SUPABASE_JWT_SECRET and not settings.SUPABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Neither SUPABASE_URL nor SUPABASE_JWT_SECRET is configured",
            )
        payload = None
        alg = "HS256"
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "HS256")
        except Exception:
            pass

        # 1. Asymmetric verification via Supabase JWKS (ES256 / RS256 for live SSO)
        if alg in ("ES256", "RS256"):
            jwks_client = _get_jwks_client()
            if jwks_client:
                try:
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=[alg],
                        options={"verify_aud": False},
                    )
                except jwt.PyJWTError as exc:
                    logger.debug("JWKS (%s) verification failed: %s", alg, exc)

        # 2. Symmetric verification via Legacy SUPABASE_JWT_SECRET or dev signing secret (HS256)
        if not payload:
            secret = _get_signing_secret()
            try:
                payload = jwt.decode(
                    token,
                    secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
            except jwt.PyJWTError as exc:
                logger.debug(
                    "Local HS256 JWT decoding failed (%s), attempting Supabase GoTrue verification...",
                    exc,
                )

        # 3. Fallback to Supabase GoTrue remote verification
        if not payload:
            payload = _verify_supabase_token_remote(token)

        if not payload:
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

        full_name = (
            user_meta.get("full_name")
            or user_meta.get("name")
            or payload.get("full_name")
            or (email.split("@")[0] if email else "Patron")
        )

        # Fetch corresponding Profile from DB or auto-provision for new Supabase SSO users
        try:
            profile = db.query(Profile).filter(Profile.id == user_id).first()
            if not profile:
                profile = Profile(
                    id=user_id,
                    email=email,
                    full_name=full_name,
                    role=role.value,
                )
                db.add(profile)
                db.commit()
                db.refresh(profile)
            return TokenUser.model_validate(profile)
        except SQLAlchemyError as exc:
            logger.debug(
                "DB profile lookup/provision failed during JWT verification: %s", exc
            )
            db.rollback()

        return TokenUser(
            id=user_id,
            email=email,
            role=role,
            full_name=full_name,
        )

    # Dev / Demo Mode Fallback when no token is passed
    if settings.DEBUG:
        return _get_or_create_user(
            email="patron@example.com",
            full_name="Demo Patron",
            role=UserRole.PATRON,
            db=db,
        )

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
