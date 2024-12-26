from sqlalchemy import Column, String, ForeignKey, JSON, Integer, Float
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserAnalytics(BaseModel):
    """Analytics model for tracking user behavior and progress."""
    
    __tablename__ = "user_analytics"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    total_sessions = Column(Integer, default=0)
    average_session_duration = Column(Float, default=0.0)
    completion_rates = Column(JSON)  # Per topic completion rates
    engagement_metrics = Column(JSON)  # Detailed engagement data
    
    # Relationship with string reference
    user = relationship("app.models.user.User", back_populates="analytics")

class TopicAnalytics(BaseModel):
    """Analytics model for tracking topic performance."""
    
    __tablename__ = "topic_analytics"
    
    id = Column(String(36), primary_key=True, index=True)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    total_interactions = Column(Integer, default=0)
    average_completion_rate = Column(Float, default=0.0)
    difficulty_ratings = Column(JSON)  # User-reported difficulty levels
    feedback_summary = Column(JSON)  # Aggregated user feedback
    
    # Relationship with string reference
    topic = relationship("app.models.topic.Topic", back_populates="analytics")

class SessionAnalytics(BaseModel):
    """Analytics model for detailed session analysis."""
    
    __tablename__ = "session_analytics"
    
    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    interaction_patterns = Column(JSON)  # Detailed interaction analysis
    performance_metrics = Column(JSON)  # Various performance indicators
    ai_insights = Column(JSON)  # AI-generated insights about the session
    
    # Relationship with string reference
    session = relationship("app.models.session.Session", back_populates="analytics") 