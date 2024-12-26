from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.chat import MessageRole

class ChatMessageCreate(BaseModel):
    content: str

class ChatMessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime
    feedback: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    has_more: bool
    total_messages: int 