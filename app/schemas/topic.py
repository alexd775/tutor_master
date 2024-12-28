from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, UUID4
from datetime import datetime

class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: dict = Field(..., description="Structured content data")
    agent_id: str = Field(..., description="Associated AI agent ID")
    difficulty_level: int = Field(1, ge=1, le=5)
    parent_id: Optional[str] = Field(None, description="Parent topic ID")

class TopicCreate(TopicBase):
    @field_validator('agent_id')
    def validate_agent_id(cls, v):
        try:
            UUID4(v)
        except ValueError:
            raise ValueError("Agent ID must be a valid UUID")
        return v

    @field_validator('parent_id')
    def validate_parent_id(cls, v):
        if v:
            try:
                UUID4(v)
            except ValueError:
                raise ValueError("Parent ID must be a valid UUID or empty")  
        return v or None

class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[dict] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)

class TopicResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    content: dict = Field(..., description="Structured content data")
    difficulty_level: int = Field(1, ge=1, le=5)
    parent_id: Optional[str] = None
    agent_id: str = Field(..., description="Associated AI agent ID")
    engagement_score: float = 0.0
    created_at: datetime
    updated_at: datetime
    subtopic_count: int = 0
    total_sessions: int = 0
    duration: int = 0
    average_completion_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True) 