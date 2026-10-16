"""Unit tests for the autonomous AI Librarian ReAct agent loop."""

from unittest.mock import MagicMock, patch
import uuid
import pytest
from pydantic_ai.models.test import TestModel

from app.core.config import settings
from app.schemas.agent import AgentChatResponse, AgentMessage
from app.services.agent_tools import LibraryContext
from app.services.librarian_agent import (
    LIBRARIAN_SYSTEM_PROMPT,
    _convert_history_to_messages,
    librarian_agent,
    run_librarian_agent,
)


def test_librarian_agent_configuration():
    """Verify librarian_agent is properly configured with tools, system prompt, and context."""
    assert librarian_agent.deps_type == LibraryContext
    assert "CRITICAL BORROWING SAFETY POLICY" in LIBRARIAN_SYSTEM_PROMPT
    assert "Claude Haiku" in LIBRARIAN_SYSTEM_PROMPT
    assert any("CRITICAL BORROWING SAFETY POLICY" in p for p in librarian_agent._system_prompts)

    # Verify all 4 tools are registered on the agent
    tool_names = list(librarian_agent._function_toolset.tools.keys())
    assert "search_catalog" in tool_names
    assert "check_availability" in tool_names
    assert "borrow_book" in tool_names
    assert "get_my_active_loans" in tool_names


def test_convert_history_to_messages():
    """Verify conversion of AgentMessage history to PydanticAI ModelMessage objects."""
    history = [
        AgentMessage(role="user", content="Hello"),
        AgentMessage(role="assistant", content="Hi, how can I help?"),
        AgentMessage(role="user", content=None),  # Empty content should be skipped
    ]
    model_msgs = _convert_history_to_messages(history)
    assert len(model_msgs) == 2
    assert model_msgs[0].parts[0].content == "Hello"
    assert model_msgs[1].parts[0].content == "Hi, how can I help?"


@pytest.mark.anyio
async def test_run_librarian_agent_offline_fallback():
    """Verify deterministic offline mock response when ANTHROPIC_API_KEY is not configured."""
    mock_db = MagicMock()
    user_id = uuid.uuid4()

    with patch.object(settings, "ANTHROPIC_API_KEY", ""):
        response = await run_librarian_agent(
            message="Find books on cloud architectures",
            user_id=user_id,
            db=mock_db,
        )
        assert isinstance(response, AgentChatResponse)
        assert "AI Librarian offline mode" in response.reply
        assert "Find books on cloud architectures" in response.reply
        assert response.tools_executed == []
        assert response.interactive_card is None


@pytest.mark.anyio
async def test_run_librarian_agent_with_test_model():
    """Verify agent execution with TestModel returns structured AgentChatResponse."""
    mock_db = MagicMock()
    user_id = uuid.uuid4()
    test_model = TestModel(custom_output_text="I found Database Internals for you!")

    response = await run_librarian_agent(
        message="Find Database Internals",
        user_id=user_id,
        db=mock_db,
        history=[AgentMessage(role="user", content="Hi")],
        override_model=test_model,
    )

    assert isinstance(response, AgentChatResponse)
    assert response.reply == "I found Database Internals for you!"
