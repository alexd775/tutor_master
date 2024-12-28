from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.agent import AgentType

class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: AgentType
    config: Dict[str, Any] = Field(..., description="Agent-specific configuration")
    system_prompt: str = Field(..., description="System prompt template")
    welcome_message: str = Field(..., description="Initial message template")
    is_active: bool = True

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[AgentType] = None
    config: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    is_active: Optional[bool] = None

class AgentResponse(AgentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 

class AgentListResponse(BaseModel):
    items: List[AgentResponse]
    total: int
