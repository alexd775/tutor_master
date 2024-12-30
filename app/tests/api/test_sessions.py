import pytest
import uuid
from app.models import Session, Topic, Agent, AgentType, User, ChatMessage
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

def test_list_all_sessions(client, superuser_token_headers, db, test_topic_with_agent):
    """Test listing all sessions (admin only)."""
    # Create some test sessions with user names
    sessions_to_create = 3
    for i in range(sessions_to_create):
        user = User(
            id=str(uuid.uuid4()),
            email=f"user{i}@example.com",
            hashed_password="hashed",
            full_name=f"Test User {i}"
        )
        db.add(user)
        db.commit()

        session = Session(
            id=str(uuid.uuid4()),
            user_id=user.id,
            topic_id=test_topic_with_agent.id,
            agent_id=test_topic_with_agent.agent_id,
            completion_rate=0.0,
            duration=i * 10
        )
        db.add(session)
    db.commit()
    
    # Test listing all sessions
    response = client.get(
        f"{settings.API_V1_STR}/sessions/all",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == sessions_to_create
    # Verify ordering (newest first)
    assert data[0]["created_at"] > data[1]["created_at"]
    # Verify user names are included
    assert all("user_full_name" in session for session in data)
    assert "Test User" in data[0]["user_full_name"]
    
    # Test filtering by topic_id
    response = client.get(
        f"{settings.API_V1_STR}/sessions/all?topic_id={test_topic_with_agent.id}",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    assert len(response.json()) == sessions_to_create
    
    # Test filtering by user_id (should return no results)
    response = client.get(
        f"{settings.API_V1_STR}/sessions/all?user_id=nonexistent",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    # Test pagination
    response = client.get(
        f"{settings.API_V1_STR}/sessions/all?limit=1",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_list_all_sessions_normal_user(client, normal_user_token_headers):
    """Test that normal users cannot list all sessions."""
    response = client.get(
        f"{settings.API_V1_STR}/sessions/all",
        headers=normal_user_token_headers
    )
    
    assert response.status_code == 403 

def test_disable_and_create_session(
    client, 
    normal_user_token_headers, 
    test_topic_with_agent,
    mock_openai,
    db
):
    """Test disabling a session and creating a new one."""
    # First create a session
    response = client.post(
        f"{settings.API_V1_STR}/sessions",
        headers=normal_user_token_headers,
        json={"topic_id": test_topic_with_agent.id}
    )
    assert response.status_code == 200
    first_session = response.json()
    
    # Now disable it and create new one
    response = client.post(
        f"{settings.API_V1_STR}/sessions/{first_session['id']}/disable",
        headers=normal_user_token_headers
    )
    
    assert response.status_code == 200
    new_session = response.json()
    
    # Verify the results
    assert new_session["id"] != first_session["id"]
    assert new_session["topic_id"] == first_session["topic_id"]
    assert new_session["completion_rate"] == 0.0
    assert new_session["is_active"] is True
    
    # Verify old session is disabled
    old_session = db.query(DBSession)\
        .filter(DBSession.id == first_session["id"])\
        .first()
    assert old_session.is_active is False
    
    # Verify new session has AI messages initialized
    messages = db.query(ChatMessage)\
        .filter(ChatMessage.session_id == new_session["id"])\
        .all()
    assert len(messages) >= 2  # Should have system and welcome messages 