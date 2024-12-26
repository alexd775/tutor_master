import pytest
from app.models import Agent, AgentType
from app.core.config import settings

def test_create_agent(client, superuser_token_headers, db):
    agent_data = {
        "name": "Test Agent",
        "type": AgentType.CHATGPT,
        "config": {
            "model": "gpt-4",
            "temperature": 0.7
        },
        "system_prompt": "You are a test agent",
        "welcome_message": "Hello, I'm a test agent"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/agents",
        headers=superuser_token_headers,
        json=agent_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agent_data["name"]
    assert data["type"] == agent_data["type"]
    
    # Verify database
    db_agent = db.query(Agent).filter(Agent.id == data["id"]).first()
    assert db_agent is not None
    assert db_agent.name == agent_data["name"]

def test_create_agent_normal_user(client, normal_user_token_headers):
    """Test that normal users cannot create agents."""
    agent_data = {
        "name": "Test Agent",
        "type": AgentType.CHATGPT,
        "config": {"model": "gpt-4"},
        "system_prompt": "Test prompt",
        "welcome_message": "Test welcome"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/agents",
        headers=normal_user_token_headers,
        json=agent_data
    )
    
    assert response.status_code == 403

@pytest.mark.parametrize(
    "invalid_data,expected_status",
    [
        ({"name": "Test", "type": "invalid_type"}, 422),
        ({"type": AgentType.CHATGPT}, 422),
        ({}, 422),
    ]
)
def test_create_agent_invalid(client, superuser_token_headers, invalid_data, expected_status):
    response = client.post(
        f"{settings.API_V1_STR}/agents",
        headers=superuser_token_headers,
        json=invalid_data
    )
    assert response.status_code == expected_status 