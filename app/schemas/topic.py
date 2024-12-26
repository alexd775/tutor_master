from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: dict = Field(..., description="Structured content data")
    agent_id: str = Field(..., description="Associated AI agent ID")
    difficulty_level: int = Field(1, ge=1, le=5)
    parent_id: Optional[str] = None

class TopicCreate(TopicBase):
    pass

class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[dict] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)

class TopicResponse(TopicBase):
    id: str
    engagement_score: float = 0.0
    created_at: datetime
    updated_at: datetime
    subtopic_count: int = 0
    total_sessions: int = 0
    average_completion_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True) 