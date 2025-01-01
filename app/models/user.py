from sqlalchemy import Boolean, Column, String, Enum as SQLEnum, ForeignKey
import enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TUTOR = "tutor"
    STUDENT = "student"

class UserPreference(BaseModel):
    """User preference model for storing user-specific settings."""
    
    __tablename__ = "user_preferences"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    theme = Column(String)
    language = Column(String)
    notifications = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="preferences")

class User(BaseModel):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships with simpler references
    sessions = relationship("Session", back_populates="user", lazy="dynamic")
    analytics = relationship("UserAnalytics", back_populates="user", lazy="dynamic")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    
    # Add these relationships
    used_invite = relationship("Invite", foreign_keys="Invite.used_by_id", back_populates="used_by", uselist=False)
    created_invites = relationship("Invite", foreign_keys="Invite.created_by_id", back_populates="created_by") 