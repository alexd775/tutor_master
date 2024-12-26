from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole

class UserPreferenceResponse(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications: bool = True

    model_config = ConfigDict(from_attributes=True) 

class UserMeResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    preferences: Optional[UserPreferenceResponse] = None
    total_sessions: int = 0
    completed_topics: int = 0

    model_config = ConfigDict(from_attributes=True) 

class UserPreferenceUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications: Optional[bool] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra = {
            "example": {
                "theme": "dark",
                "language": "en",
                "notifications": True
            }
        }
    )
