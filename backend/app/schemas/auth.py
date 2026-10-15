from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRole(str, Enum):
    """Enumeration of user authorization roles in the library system."""

    PATRON = "PATRON"
    LIBRARIAN = "LIBRARIAN"


class TokenUser(BaseModel):
    """Authenticated user payload extracted from Supabase JWT claims or session."""

    # Enable attribute-based mapping to allow direct instantiation from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole = UserRole.PATRON
    full_name: str | None = None


class DemoTokenRequest(BaseModel):
    """Request payload for issuing a demo user JWT."""

    role: UserRole = UserRole.PATRON


class TokenResponse(BaseModel):
    """Response payload containing JWT bearer token and user claims."""

    access_token: str
    token_type: str = "bearer"
    user: TokenUser
