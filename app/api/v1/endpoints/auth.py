from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserCreate, UserResponse
import uuid

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    db: Annotated[Session, Depends(deps.get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """OAuth2 compatible token login."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(
        user.id, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(user.id)
    
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
) -> Token:
    """Refresh access token."""
    access_token = create_access_token(current_user.id)
    refresh_token = create_refresh_token(current_user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/register", response_model=UserResponse)
async def register(
    *,
    db: Annotated[Session, Depends(deps.get_db)],
    user_in: UserCreate,
) -> User:
    """Register new user."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    
    user = User(
        id=str(uuid.uuid4()),
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.STUDENT,  # Default role for new users
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/verify", response_model=UserResponse)
async def verify_token(
    current_user: Annotated[User, Depends(deps.get_current_user)]
) -> User:
    """Verify access token and return user info."""
    return current_user 