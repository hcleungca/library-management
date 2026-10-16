"""Unit tests for Autonomous AI Librarian chat schemas."""

import json
import pytest
from pydantic import ValidationError

from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentMessage,
    ToolExecutionRecord,
)


def test_agent_message_valid():
    """Verify valid AgentMessage roles and content."""
    msg_user = AgentMessage(role="user", content="Hello, can you help me find a book?")
    assert msg_user.role == "user"
    assert msg_user.content == "Hello, can you help me find a book?"

    msg_assistant = AgentMessage(role="assistant", content="Sure! What topic are you interested in?")
    assert msg_assistant.role == "assistant"

    msg_system = AgentMessage(role="system", content="You are a helpful librarian.")
    assert msg_system.role == "system"


def test_agent_message_invalid_role():
    """Verify AgentMessage rejects unapproved roles."""
    with pytest.raises(ValidationError):
        AgentMessage(role="invalid_role", content="Test")


def test_tool_execution_record():
    """Verify ToolExecutionRecord captures tool name, arguments, and result."""
    record = ToolExecutionRecord(
        tool_name="search_catalog",
        arguments={"query": "distributed systems", "limit": 3},
        result=[{"id": 4, "title": "Database Internals"}],
    )
    assert record.tool_name == "search_catalog"
    assert record.arguments["query"] == "distributed systems"
    assert len(record.result) == 1


def test_agent_chat_request_valid_and_defaults():
    """Verify AgentChatRequest default history and validation boundaries."""
    req = AgentChatRequest(message="Recommend books on cloud infrastructure")
    assert req.message == "Recommend books on cloud infrastructure"
    assert req.history == []

    # With conversation history
    req_with_history = AgentChatRequest(
        message="Yes, please borrow it",
        history=[
            AgentMessage(role="user", content="Find Database Internals"),
            AgentMessage(role="assistant", content="I found it! Would you like me to borrow it?"),
        ],
    )
    assert len(req_with_history.history) == 2
    assert req_with_history.history[0].role == "user"
    assert req_with_history.history[1].role == "assistant"


def test_agent_chat_request_validation_errors():
    """Verify AgentChatRequest empty message triggers ValidationError."""
    with pytest.raises(ValidationError):
        AgentChatRequest(message="")


def test_agent_chat_response_with_interactive_cards():
    """Verify AgentChatResponse supports confirm_borrow, book_list, and active_loans cards."""
    # 1. Single-book Human-in-the-Loop confirmation card
    borrow_card = {
        "type": "CONFIRM_BORROW",
        "book_id": 4,
        "title": "Database Internals",
        "author": "Alex Petrov",
        "cover_image_url": "https://example.com/cover.jpg",
        "due_days": 14,
    }
    tool_rec = ToolExecutionRecord(
        tool_name="check_availability",
        arguments={"book_id": 4},
        result={"status": "AVAILABLE", "is_available": True},
    )

    resp_borrow = AgentChatResponse(
        reply="I found 'Database Internals' available on the stacks! Would you like me to check it out for you?",
        tools_executed=[tool_rec],
        interactive_card=borrow_card,
    )
    assert resp_borrow.interactive_card["type"] == "CONFIRM_BORROW"
    assert resp_borrow.interactive_card["book_id"] == 4
    assert len(resp_borrow.tools_executed) == 1

    # 2. Multi-book candidate list card
    list_card = {
        "type": "BOOK_LIST",
        "books": [
            {"id": 4, "title": "Database Internals", "status": "AVAILABLE"},
            {"id": 6, "title": "Building Microservices", "status": "AVAILABLE"},
        ],
    }
    resp_list = AgentChatResponse(
        reply="Here are two relevant books on distributed architecture:",
        tools_executed=[],
        interactive_card=list_card,
    )
    assert resp_list.interactive_card["type"] == "BOOK_LIST"
    assert len(resp_list.interactive_card["books"]) == 2

    # 3. Verify clean JSON serialization and round-trip parsing
    json_str = resp_borrow.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["reply"].startswith("I found 'Database Internals'")
    assert parsed["interactive_card"]["type"] == "CONFIRM_BORROW"
    assert parsed["tools_executed"][0]["tool_name"] == "check_availability"

    revalidated = AgentChatResponse.model_validate_json(json_str)
    assert revalidated.interactive_card["book_id"] == 4


def test_convert_history_merges_consecutive_roles():
    """Verify _convert_history_to_messages collapses consecutive roles and guarantees alternation."""
    from app.services.librarian_agent import _convert_history_to_messages
    from pydantic_ai.messages import ModelRequest, ModelResponse

    history = [
        AgentMessage(role="assistant", content="Leading assistant message to drop"),
        AgentMessage(role="user", content="Recommend books"),
        AgentMessage(role="assistant", content="Here is Petrov"),
        AgentMessage(role="assistant", content="✓ Checkout confirmed"),
    ]
    model_msgs = _convert_history_to_messages(history)
    assert len(model_msgs) == 2
    assert isinstance(model_msgs[0], ModelRequest)
    assert model_msgs[0].parts[0].content == "Recommend books"
    assert isinstance(model_msgs[1], ModelResponse)
    assert "Here is Petrov" in model_msgs[1].parts[0].content
    assert "✓ Checkout confirmed" in model_msgs[1].parts[0].content


