from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class SessionBase(BaseModel):
    topic_id: str
    duration: Optional[int] = 0
    completion_rate: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    interaction_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    feedback_score: Optional[int] = Field(None, ge=1, le=5)

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    duration: Optional[int] = None
    completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    interaction_data: Optional[Dict[str, Any]] = None
    feedback_score: Optional[int] = Field(None, ge=1, le=5)

class SessionResponse(SessionBase):
    id: str
    user_id: str
    completion_rate: float
    created_at: datetime
    topic_title: Optional[str] = None
    user_full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) 