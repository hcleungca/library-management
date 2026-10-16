"""AI Librarian conversational agent API router.

Exposes endpoints for patrons to converse with the autonomous AI Librarian powered
by PydanticAI and Claude Haiku, receiving recommendations, inventory availability,
and Human-in-the-Loop checkout confirmation cards.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.auth import TokenUser
from app.services.librarian_agent import run_librarian_agent

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/agent", response_model=AgentChatResponse)
async def chat_with_librarian(
    req: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
) -> AgentChatResponse:
    """Converse with the autonomous AI Librarian.

    Executes multi-step reasoning over catalog books, checking availability,
    and enforcing Human-in-the-Loop borrowing safety.
    """
    response = await run_librarian_agent(
        message=req.message,
        user_id=current_user.id,
        user_role=current_user.role.value,
        db=db,
        history=req.history,
    )
    return response

