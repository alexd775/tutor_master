from sqlalchemy import Column, String, JSON, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel

class AgentType(str, enum.Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    CUSTOM = "custom"

class Agent(BaseModel):
    """AI Agent configuration model."""
    
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(AgentType), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # ai service
    ai_service = Column(String, nullable=True, default="openai")
    # Agent-specific configuration
    config = Column(JSON, nullable=False)
    
    # System prompt template
    system_prompt = Column(Text, nullable=False)
    # Initial message template
    welcome_message = Column(Text, nullable=False)
    # Reminder message template
    reminder_message = Column(Text, nullable=True)
    
    # Relationships
    topics = relationship("Topic", back_populates="agent")
    sessions = relationship("Session", back_populates="agent")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python Tutor",
                "type": "chatgpt",
                "config": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                "system_prompt": "You are an expert Python tutor...",
                "welcome_message": "Hello! I'm your Python tutor..."
            }
        } 