import pytest
import uuid
from app.core.config import settings
from app.models import Session as DBSession, Agent, AgentType, Topic

@pytest.fixture
def test_topic_with_agent(db):
    agent = Agent(
        id=str(uuid.uuid4()),
        name="Test Agent",
        type=AgentType.CHATGPT,
        config={"model": "gpt-4"},
        system_prompt="Test prompt",
        welcome_message="Test welcome",
        is_active=True
    )
    
    topic = Topic(
        id=str(uuid.uuid4()),
        title="Test Topic",
        content={},
        agent_id=agent.id
    )
    
    db.add(agent)
    db.add(topic)
    db.commit()
    return topic

@pytest.fixture
def test_session(client, normal_user_token_headers, test_topic_with_agent, db):
    """Create a test session."""
    response = client.post(
        f"{settings.API_V1_STR}/sessions",
        headers=normal_user_token_headers,
        json={"topic_id": test_topic_with_agent.id}
    )
    assert response.status_code == 200
    return response.json()

def test_send_message(client, normal_user_token_headers, test_session, mock_openai):
    """Test sending a message in chat."""
    message = {
        "content": "Hello, I need help with Python!"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/chat/sessions/{test_session['id']}/chat",
        headers=normal_user_token_headers,
        json=message
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data[1]["role"] == "assistant"
    assert data[1]["content"] == "Mocked AI response"
    
    # Verify OpenAI was called correctly
    mock_openai.assert_called_once()
    call_args = mock_openai.call_args[1]
    assert "messages" in call_args
    assert call_args["model"] == "gpt-4"

def test_get_chat_history(client, normal_user_token_headers, test_session, db, mock_openai):
    """Test retrieving chat history."""
    # First send a message
    message = {"content": "Test message"}
    client.post(
        f"{settings.API_V1_STR}/chat/sessions/{test_session['id']}/chat",
        headers=normal_user_token_headers,
        json=message
    )
    
    # Get history
    response = client.get(
        f"{settings.API_V1_STR}/chat/sessions/{test_session['id']}/chat",
        headers=normal_user_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert data["total_messages"] > 0
    assert len(data["messages"]) > 0

def test_send_message_invalid_session(client, normal_user_token_headers):
    """Test sending message to invalid session."""
    message = {"content": "Test message"}
    response = client.post(
        f"{settings.API_V1_STR}/chat/sessions/invalid-id/chat",
        headers=normal_user_token_headers,
        json=message
    )
    
    assert response.status_code == 404 