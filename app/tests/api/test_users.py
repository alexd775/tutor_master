import uuid
from app.core.config import settings
from app.models import User

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