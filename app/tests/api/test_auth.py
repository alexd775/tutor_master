import pytest
from app.core.config import settings

def test_login(client, db):
    """Test user login."""
    # First create a user
    user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data
    )
    assert response.status_code == 200
    
    # Try logging in
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, db):
    """Test login with wrong password."""
    login_data = {
        "username": "test@example.com",
        "password": "wrongpass"
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_refresh_token(client, normal_user_token_headers):
    """Test token refresh."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data 