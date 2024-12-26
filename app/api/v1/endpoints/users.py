from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User, UserPreference, UserRole
from app.schemas.user import UserMeResponse, UserPreferenceUpdate, UserPreferenceResponse
from sqlalchemy import func
from app.models import Session as DBSession
import uuid

router = APIRouter()

@router.get("/me", response_model=UserMeResponse)
async def read_user_me(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)]
) -> User:
    """Get current user information with additional stats."""
    # Get total sessions count
    total_sessions = db.query(func.count(DBSession.id))\
        .filter(DBSession.user_id == current_user.id)\
        .scalar()

    # Get completed topics count (topics with completion_rate >= 0.8)
    completed_topics = db.query(func.count(DBSession.topic_id.distinct()))\
        .filter(
            DBSession.user_id == current_user.id,
            DBSession.completion_rate >= 0.8
        ).scalar()

    # Attach the computed stats to the user object
    setattr(current_user, 'total_sessions', total_sessions or 0)
    setattr(current_user, 'completed_topics', completed_topics or 0)
    
    return current_user 

@router.put("/me/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    *,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[Session, Depends(deps.get_db)],
    preferences: UserPreferenceUpdate
) -> UserPreferenceResponse:
    """Update current user preferences."""
    if not current_user.preferences:
        # Create new preferences if they don't exist
        db_preferences = UserPreference(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            **preferences.model_dump(exclude_unset=True)
        )
        db.add(db_preferences)
    else:
        # Update existing preferences
        for key, value in preferences.model_dump(exclude_unset=True).items():
            setattr(current_user.preferences, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user.preferences 

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: Annotated[User, Depends(deps.get_current_active_superuser)],
    db: Annotated[Session, Depends(deps.get_db)]
) -> dict:
    """Deactivate a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate admin users"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

