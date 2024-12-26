import pytest
import uuid
from app.models import Session, Topic, Agent, AgentType
from app.core.config import settings

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

def test_create_session(client, normal_user_token_headers, db, test_topic_with_agent):
    session_data = {
        "topic_id": test_topic_with_agent.id
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/sessions",
        headers=normal_user_token_headers,
        json=session_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["topic_id"] == test_topic_with_agent.id
    
    # Verify database
    db_session = db.query(Session).filter(Session.id == data["id"]).first()
    assert db_session is not None
    assert db_session.agent_id == test_topic_with_agent.agent_id

def test_create_duplicate_session(client, normal_user_token_headers, db, test_topic_with_agent):
    """Test that users cannot create multiple active sessions for the same topic."""
    session_data = {
        "topic_id": test_topic_with_agent.id
    }
    
    # Create first session
    response1 = client.post(
        f"{settings.API_V1_STR}/sessions",
        headers=normal_user_token_headers,
        json=session_data
    )
    assert response1.status_code == 200
    
    # Try to create second session
    response2 = client.post(
        f"{settings.API_V1_STR}/sessions",
        headers=normal_user_token_headers,
        json=session_data
    )
    assert response2.status_code == 400
    assert "Active session already exists" in response2.json()["detail"]["message"] 