from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum, JSON, Integer
from sqlalchemy.orm import relationship

import enum
from app.models.base import BaseModel

class MessageRole(str, enum.Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"

class ChatMessage(BaseModel):
    """Model for storing chat messages."""
    
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"))
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Metadata for tracking
    tokens = Column(Integer, default=0)
    feedback = Column(JSON, nullable=True)  # For storing user reactions, flags, etc.
    
    session = relationship("Session", back_populates="messages") 