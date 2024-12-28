import uuid
from app.core.config import settings
from app.models import User
from app.models.session import Session as DBSession
from app.models.user import UserRole

def test_read_current_user(client, normal_user_token_headers):
    """Test getting current user info."""
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"

def test_update_preferences(client, normal_user_token_headers):
    """Test updating user preferences."""
    preferences = {
        "theme": "dark",
        "language": "es",
        "notifications": False
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me/preferences",
        headers=normal_user_token_headers,
        json=preferences
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == preferences["theme"]
    assert data["language"] == preferences["language"]
    assert data["notifications"] == preferences["notifications"]

def test_deactivate_user(client, superuser_token_headers, db):
    """Test user deactivation (admin only)."""
    # Create a user to deactivate
    user = User(
        id=str(uuid.uuid4()),
        email="todeactivate@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()
    
    response = client.post(
        f"{settings.API_V1_STR}/users/{user.id}/deactivate",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    db.refresh(user)
    assert not user.is_active 

def test_list_users(client, superuser_token_headers, db):
    """Test listing all users with filters."""
    # Create test users with different roles and statuses
    test_users = [
        {
            "email": "student1@example.com",
            "hashed_password": "hashed",
            "full_name": "Student 1",
            "role": UserRole.STUDENT,
            "is_active": True
        },
        {
            "email": "student2@example.com",
            "hashed_password": "hashed",
            "full_name": "Student 2",
            "role": UserRole.STUDENT,
            "is_active": False
        },
        {
            "email": "teacher@example.com",
            "hashed_password": "hashed",
            "full_name": "Teacher",
            "role": UserRole.TUTOR,
            "is_active": True
        }
    ]
    
    for user_data in test_users:
        user = User(id=str(uuid.uuid4()), **user_data)
        db.add(user)
    db.commit()
    
    # Create some sessions for the first user
    first_user = db.query(User).filter(User.email == "student1@example.com").first()
    for _ in range(3):
        session = DBSession(
            id=str(uuid.uuid4()),
            user_id=first_user.id,
            topic_id=str(uuid.uuid4()),
            agent_id=str(uuid.uuid4())
        )
        db.add(session)
    db.commit()
    
    # Test listing all users
    response = client.get(
        f"{settings.API_V1_STR}/users/all",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # At least our test users
    
    # Test filtering by role
    response = client.get(
        f"{settings.API_V1_STR}/users/all?role=student",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(user["role"] == UserRole.STUDENT for user in data)
    
    # Test filtering by active status
    response = client.get(
        f"{settings.API_V1_STR}/users/all?is_active=true",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert all(user["is_active"] for user in data)
    
    # Verify session counts
    first_user_data = next(
        user for user in data 
        if user["email"] == "student1@example.com"
    )
    assert first_user_data["total_sessions"] == 3

def test_list_users_normal_user(client, normal_user_token_headers):
    """Test that normal users cannot list all users."""
    response = client.get(
        f"{settings.API_V1_STR}/users/all",
        headers=normal_user_token_headers
    )
    
    assert response.status_code == 403 