import pytest
import uuid
from app.core.config import settings
from app.models import Topic, Agent, AgentType, Session as DBSession, ChatMessage, MessageRole

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

def test_get_or_create_session(
    client, 
    normal_user_token_headers, 
    test_topic_with_agent,
    mock_openai,
    db
):
    """Test getting or creating a session for a topic."""
    # First request should create a new session
    response = client.get(
        f"{settings.API_V1_STR}/topics/{test_topic_with_agent.id}/session",
        headers=normal_user_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["topic_id"] == test_topic_with_agent.id
    assert data["completion_rate"] == 0.0
    assert "topic_title" in data
    first_session_id = data["id"]
    
    # Second request should return the same session
    response = client.get(
        f"{settings.API_V1_STR}/topics/{test_topic_with_agent.id}/session",
        headers=normal_user_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_session_id  # Same session returned

def test_get_session_invalid_topic(client, normal_user_token_headers):
    """Test getting session for non-existent topic."""
    response = client.get(
        f"{settings.API_V1_STR}/topics/invalid-id/session",
        headers=normal_user_token_headers
    )
    
    assert response.status_code == 404
    assert "Topic not found" in response.json()["detail"] 

def test_delete_topic_cascade(client, superuser_token_headers, db, test_agent):
    """Test deleting a topic cascades to subtopics, sessions, and chat messages."""
    # Create parent topic
    parent_topic = Topic(
        id=str(uuid.uuid4()),
        title="Parent Topic",
        content={},
        agent_id=test_agent.id
    )
    db.add(parent_topic)
    db.commit()
    db.refresh(parent_topic)
    
    # Create subtopic
    subtopic = Topic(
        id=str(uuid.uuid4()),
        title="Subtopic",
        content={},
        agent_id=test_agent.id,
        parent_id=parent_topic.id
    )
    db.add(subtopic)
    db.commit()
    db.refresh(subtopic)
    
    # Create sessions for both topics
    parent_session = DBSession(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        topic_id=parent_topic.id,
        agent_id=test_agent.id
    )
    subtopic_session = DBSession(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        topic_id=subtopic.id,
        agent_id=test_agent.id
    )
    db.add_all([parent_session, subtopic_session])
    db.commit()
    
    # Store IDs for verification
    parent_id = parent_topic.id
    subtopic_id = subtopic.id
    session_ids = [parent_session.id, subtopic_session.id]
    
    # Delete parent topic
    response = client.delete(
        f"{settings.API_V1_STR}/topics/{parent_id}",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["deleted_topics"] == 2
    assert data["deleted_sessions"] == 2
    
    # Verify everything is deleted using fresh queries
    assert db.query(Topic).filter(Topic.id.in_([parent_id, subtopic_id])).count() == 0
    assert db.query(DBSession).filter(DBSession.id.in_(session_ids)).count() == 0

def test_delete_topic_rollback(client, superuser_token_headers, db, test_agent):
    """Test that deletion rolls back on error."""
    # Create test data
    parent_topic = Topic(
        id=str(uuid.uuid4()),
        title="Parent Topic",
        content={},
        agent_id=test_agent.id
    )
    db.add(parent_topic)
    db.commit()
    db.refresh(parent_topic)
    
    topic_id = parent_topic.id
    
    # Mock query to raise an error
    original_query = db.query
    def mock_query(*args):
        result = original_query(*args)
        if args and args[0] == ChatMessage:
            raise Exception("Simulated error")
        return result
    
    db.query = mock_query
    
    # Try to delete topic
    response = client.delete(
        f"{settings.API_V1_STR}/topics/{topic_id}",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 500
    assert "Failed to delete topic" in response.json()["detail"]
    
    # Restore original query method
    db.query = original_query
    
    # Verify nothing was deleted (rollback worked)
    db.refresh(db.query(Topic).get(topic_id))
    assert db.query(Topic).filter(Topic.id == topic_id).first() is not None 