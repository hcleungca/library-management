"""Authentication and demo token generation endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import create_demo_jwt, create_sso_jwt
from app.db.session import get_db
from app.schemas.auth import DemoTokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-token", response_model=TokenResponse)
def get_demo_token(
    payload: DemoTokenRequest | None = None,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Issue an authentic signed JWT bearer token for the specified demo user role.

    Allows reviewers and frontend role switchers to acquire genuine access tokens
    for PATRON and LIBRARIAN accounts across all environments.
    """
    req = payload or DemoTokenRequest()
    token, user = create_demo_jwt(role=req.role, db=db)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.post("/sso-token", response_model=TokenResponse)
def get_sso_token(
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Issue an authentic signed JWT bearer token for a library patron authenticated via SSO."""
    token, user = create_sso_jwt(db=db)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.get("/config")
def get_auth_config() -> dict[str, str]:
    """Return public Supabase configuration for frontend OAuth client initialization."""
    from app.core.config import settings

    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_KEY,
    }
