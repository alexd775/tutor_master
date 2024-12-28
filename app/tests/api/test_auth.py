import pytest
from app.core.config import settings
from datetime import timedelta
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from jose.exceptions import JWTError
from app.core.security import create_access_token

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
    # First get a refresh token through login
    login_data = {
        "username": "user@example.com",
        "password": "user_password"
    }
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Use refresh token to get new tokens
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_refresh_token_invalid(client):
    """Test refresh with invalid token."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"] 

def test_verify_access_token(client, normal_user_token_headers):
    """Test verifying a valid access token."""
    # First get an access token through login
    login_data = {
        "username": "user@example.com",
        "password": "user_password"
    }
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    access_token = login_response.json()["access_token"]
    
    # Verify the token
    response = client.post(
        f"{settings.API_V1_STR}/auth/verify",
        json={"token": access_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["token_type"] == "access"
    assert "user_id" in data

def test_verify_refresh_token(client, normal_user_token_headers):
    """Test verifying a valid refresh token."""
    login_data = {
        "username": "user@example.com",
        "password": "user_password"
    }
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    refresh_token = login_response.json()["refresh_token"]
    
    response = client.post(
        f"{settings.API_V1_STR}/auth/verify",
        json={"token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["token_type"] == "refresh"
    assert "user_id" in data

def test_verify_invalid_token(client):
    """Test verifying an invalid token."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/verify",
        json={"token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]

def test_verify_expired_token(client):
    """Test verifying an expired token."""
    # Create an expired token
    expired_token = create_access_token(
        "some_user_id",
        expires_delta=timedelta(minutes=-1)  # Expired 1 minute ago
    )
    
    response = client.post(
        f"{settings.API_V1_STR}/auth/verify",
        json={"token": expired_token}
    )
    
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"] 