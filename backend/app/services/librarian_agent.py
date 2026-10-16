"""Autonomous AI Librarian Multi-Step ReAct Agent Service.

Powered by PydanticAI and Claude Haiku. Plans and executes multi-step tool calls
against PostgreSQL and pgvector with strict Human-in-the-Loop borrowing safety.
"""

import os
from typing import Any
from uuid import UUID
import logging

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.agent import AgentChatResponse, AgentMessage
from app.services.agent_tools import (
    LibraryContext,
    borrow_book,
    check_availability,
    get_my_active_loans,
    search_catalog,
)

# Suppress PydanticAI banner in non-interactive/CLI execution
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

logger = logging.getLogger(__name__)

LIBRARIAN_SYSTEM_PROMPT = (
    "You are the Intelligent Library AI Assistant powered by Claude Haiku.\n"
    "You help patrons discover books, check inventory availability, and manage loans.\n\n"
    "CRITICAL BORROWING SAFETY POLICY:\n"
    "- You MUST NEVER execute borrow_book without explicit user confirmation.\n"
    "- When a user asks to borrow a book, first check availability with check_availability.\n"
    "- If available, present the book details and ask: 'Would you like me to confirm this checkout for you?'\n"
    "- Only call borrow_book after the user explicitly confirms (e.g., 'yes', 'confirm', 'go ahead', or clicks the confirmation card).\n"
    "- LIBRARIAN BORROWING RESTRICTION: If the user is a LIBRARIAN, they cannot borrow books. Politely inform them that only patrons may check out books, though you can still help them check inventory.\n\n"
    "CATALOG SEARCH GUIDELINES:\n"
    "- For book recommendations or topic inquiries, call search_catalog with the user's natural language concept or genre.\n"
    "- For questions regarding the patron's current checkouts, call get_my_active_loans.\n"
    "- Always be polite, helpful, and concise.\n\n"
    "FORMATTING & MARKDOWN GUIDELINES:\n"
    "- Always format your responses using clean, readable GitHub-flavored Markdown.\n"
    "- Use bold (**Book Title**) for titles and key terms.\n"
    "- Use bullet points (- ) or numbered lists for book recommendations and steps.\n"
    "- Use clear section headings (e.g., ### Best Matches) to organize multi-book recommendations.\n"
    "- Keep responses structured, concise, and easy to skim."
)


def _build_model() -> Any:
    """Build the Anthropic Claude Haiku model or TestModel if API key is not configured."""
    if settings.ANTHROPIC_API_KEY:
        try:
            return AnthropicModel(
                settings.ANTHROPIC_MODEL,
                provider=AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY),
            )
        except Exception as exc:
            logger.warning("Failed to initialize AnthropicModel: %s. Using TestModel.", exc)
    return TestModel()


# Global agent instance with bound tools
librarian_agent: Agent[LibraryContext, str] = Agent(
    model=_build_model(),
    deps_type=LibraryContext,
    system_prompt=LIBRARIAN_SYSTEM_PROMPT,
    tools=[search_catalog, check_availability, borrow_book, get_my_active_loans],
)


def _convert_history_to_messages(history: list[AgentMessage]) -> list[ModelMessage]:
    """Convert API AgentMessage history into PydanticAI ModelMessage objects.

    Guarantees strict alternating user/assistant turns required by LLM providers
    (e.g., Anthropic Claude). Merges consecutive messages with the same role and
    ensures history begins with a user turn.
    """
    messages: list[ModelMessage] = []
    for msg in history:
        if not msg.content or not msg.content.strip():
            continue
        if msg.role == "user":
            if messages and isinstance(messages[-1], ModelRequest):
                # Consecutive user messages: concatenate text into existing request
                last_part = messages[-1].parts[-1]
                if isinstance(last_part, UserPromptPart) and isinstance(last_part.content, str):
                    last_part.content = f"{last_part.content}\n\n{msg.content}"
                else:
                    messages[-1].parts.append(UserPromptPart(content=msg.content))
            else:
                messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
        elif msg.role == "assistant":
            if messages and isinstance(messages[-1], ModelResponse):
                # Consecutive assistant messages: concatenate text into existing response
                last_part = messages[-1].parts[-1]
                if isinstance(last_part, TextPart):
                    last_part.content = f"{last_part.content}\n\n{msg.content}"
                else:
                    messages[-1].parts.append(TextPart(content=msg.content))
            else:
                messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))

    # LLM APIs (e.g. Anthropic) require conversation history to start with a user message
    while messages and isinstance(messages[0], ModelResponse):
        messages.pop(0)

    return messages


async def run_librarian_agent(
    message: str,
    user_id: UUID,
    db: Session,
    user_role: str = "PATRON",
    history: list[AgentMessage] | None = None,
    override_model: Any = None,
) -> AgentChatResponse:
    """Execute the multi-step autonomous agent loop for a user conversation turn.

    1. Initializes LibraryContext dependency container with user identity and role.
    2. Checks for ANTHROPIC_API_KEY; falls back to deterministic mock response if unconfigured.
    3. Runs PydanticAI agent ReAct loop with tools and multi-turn message history.
    4. Returns AgentChatResponse containing text reply, tool audit trace, and interactive cards.
    """
    deps = LibraryContext(
        db=db,
        user_id=user_id,
        user_role=user_role,
        tools_executed=[],
        interactive_card=None,
    )

    # Fallback when Anthropic API key is not configured and no override model is passed
    if not settings.ANTHROPIC_API_KEY and override_model is None:
        return AgentChatResponse(
            reply=f"AI Librarian offline mode. Received: '{message}'",
            tools_executed=[],
            interactive_card=None,
        )

    # Convert conversation history with strict role alternation
    message_history = _convert_history_to_messages(history or [])

    # If history ends with a user request, merge it into message to prevent consecutive user turns
    effective_message = message
    if message_history and isinstance(message_history[-1], ModelRequest):
        last_req = message_history.pop()
        user_texts = [
            p.content for p in last_req.parts if isinstance(p, UserPromptPart) and isinstance(p.content, str)
        ]
        if user_texts:
            joined_user_texts = "\n\n".join(user_texts)
            effective_message = f"{joined_user_texts}\n\n{message}"

    try:
        run_kwargs: dict[str, Any] = {
            "deps": deps,
            "message_history": message_history,
        }
        if override_model is not None:
            run_kwargs["model"] = override_model

        result = await librarian_agent.run(effective_message, **run_kwargs)

        output_text = getattr(result, "output", None) or getattr(result, "data", None) or ""

        return AgentChatResponse(
            reply=str(output_text),
            tools_executed=deps.tools_executed,
            interactive_card=deps.interactive_card,
        )

    except Exception as exc:
        logger.error("Error running AI Librarian agent loop: %s", exc, exc_info=True)
        return AgentChatResponse(
            reply=f"I encountered an error processing your request: {exc}",
            tools_executed=deps.tools_executed,
            interactive_card=deps.interactive_card,
        )

