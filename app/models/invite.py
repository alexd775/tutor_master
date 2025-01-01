from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Invite(BaseModel):
    """Model for storing invitation codes."""
    
    __tablename__ = "invites"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    used_by = relationship("User", foreign_keys=[used_by_id], back_populates="used_invite")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_invites") 