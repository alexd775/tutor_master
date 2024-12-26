import pytest
import uuid
from app.core.config import settings
from app.models import Topic, Agent, AgentType

@pytest.fixture
def test_agent(db):
    agent = Agent(
        id=str(uuid.uuid4()),
        name="Test Agent",
        type=AgentType.CHATGPT,
        config={"model": "gpt-4"},
        system_prompt="Test prompt",
        welcome_message="Test welcome",
        is_active=True
    )
    db.add(agent)
    db.commit()
    return agent

def test_create_topic(client, superuser_token_headers, db, test_agent):
    topic_data = {
        "title": "Test Topic",
        "description": "Test Description",
        "content": {"key": "value"},
        "agent_id": test_agent.id,
        "difficulty_level": 2
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/topics",
        headers=superuser_token_headers,
        json=topic_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == topic_data["title"]
    assert data["agent_id"] == test_agent.id
    
    # Verify database
    db_topic = db.query(Topic).filter(Topic.id == data["id"]).first()
    assert db_topic is not None
    assert db_topic.title == topic_data["title"]

def test_create_topic_inactive_agent(client, superuser_token_headers, db, test_agent):
    # Make agent inactive
    test_agent.is_active = False
    db.commit()
    
    topic_data = {
        "title": "Test Topic",
        "content": {"key": "value"},
        "agent_id": test_agent.id
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/topics",
        headers=superuser_token_headers,
        json=topic_data
    )
    
    assert response.status_code == 400
    assert "Agent is not active" in response.json()["detail"] 