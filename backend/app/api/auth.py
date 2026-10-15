"""Authentication and demo token generation endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import create_demo_jwt
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
