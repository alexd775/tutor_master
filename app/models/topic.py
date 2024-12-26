from sqlalchemy import Column, String, JSON, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
from app.models.base import BaseModel

class Topic(BaseModel):
    """Topic model for managing learning content."""

    __tablename__ = "topics"
    
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    content = Column(JSON)  # Structured content data
    difficulty_level = Column(Integer, nullable=False, default=1)
    parent_id = Column(String(36), ForeignKey("topics.id"), nullable=True)
    engagement_score = Column(Float, default=0.0)  # Calculated based on user interactions
    
    # Self-referential relationship for topic hierarchy
    subtopics = relationship(
        "Topic",
        backref=backref("parent", remote_side=[id]),
        cascade="all",
        lazy="dynamic"
    )
    
    # Relationships
    sessions = relationship("Session", back_populates="topic")
    analytics = relationship("TopicAnalytics", back_populates="topic")
    
    # Add agent relationship
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True)
    agent = relationship("Agent", back_populates="topics") 