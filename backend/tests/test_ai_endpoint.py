"""Unit tests for the AI Librarian chat endpoint (/api/ai/agent)."""

from unittest.mock import AsyncMock, patch
import uuid
from fastapi.testclient import TestClient

from app.core.auth import create_demo_jwt
from app.main import app
from app.schemas.agent import AgentChatResponse, ToolExecutionRecord
from app.schemas.auth import UserRole

client = TestClient(app)


def test_ai_agent_route_registered():
    """Verify /api/ai/agent route is registered in the FastAPI app with POST method."""
    openapi_paths = app.openapi()["paths"]
    assert "/api/ai/agent" in openapi_paths
    assert "post" in openapi_paths["/api/ai/agent"]


def test_chat_with_librarian_unauthenticated():
    """Verify unauthenticated request to /api/ai/agent returns 401 Unauthorized."""
    response = client.post("/api/ai/agent", json={"message": "Recommend a book"})
    assert response.status_code == 401


@patch("app.api.ai.run_librarian_agent", new_callable=AsyncMock)
def test_chat_with_librarian_authenticated(mock_run_agent):
    """Verify authenticated request invokes run_librarian_agent and returns AgentChatResponse."""
    token, user = create_demo_jwt(UserRole.PATRON)

    mock_run_agent.return_value = AgentChatResponse(
        reply="I found Database Internals for you! Would you like me to borrow it?",
        tools_executed=[
            ToolExecutionRecord(
                tool_name="search_catalog",
                arguments={"query": "distributed systems"},
                result=[{"id": 4, "title": "Database Internals"}],
            )
        ],
        interactive_card={
            "type": "CONFIRM_BORROW",
            "book_id": 4,
            "title": "Database Internals",
        },
    )

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": "Find books on distributed systems",
        "history": [],
    }

    response = client.post("/api/ai/agent", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["reply"].startswith("I found Database Internals")
    assert len(data["tools_executed"]) == 1
    assert data["tools_executed"][0]["tool_name"] == "search_catalog"
    assert data["interactive_card"]["type"] == "CONFIRM_BORROW"
    assert data["interactive_card"]["book_id"] == 4

    # Verify run_librarian_agent was called with the authenticated patron's user_id
    mock_run_agent.assert_called_once()
    _, kwargs = mock_run_agent.call_args
    assert kwargs["user_id"] == user.id
    assert kwargs["user_role"] == "PATRON"
    assert kwargs["message"] == "Find books on distributed systems"


def test_chat_with_librarian_validation_error():
    """Verify empty message payload returns 422 Unprocessable Entity."""
    token, _ = create_demo_jwt(UserRole.PATRON)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/ai/agent", json={"message": ""}, headers=headers)
    assert response.status_code == 422

