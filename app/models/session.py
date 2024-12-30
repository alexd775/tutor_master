from sqlalchemy import Column, String, ForeignKey, JSON, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Session(BaseModel):
    """Session model for tracking user learning activities."""
    
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    duration = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    interaction_data = Column(JSON)
    feedback_score = Column(Integer, nullable=True)
    
    # Relationships with simpler references
    user = relationship("User", back_populates="sessions")
    topic = relationship("Topic", back_populates="sessions")
    analytics = relationship("SessionAnalytics", back_populates="session")
    
    # Add agent and chat relationships
    agent_id = Column(String(36), ForeignKey("agents.id"))
    agent = relationship("Agent", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")
    
    # Add agent state/context
    agent_state = Column(JSON, default=dict)  # Store agent-specific state 