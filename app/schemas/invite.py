from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class InviteBase(BaseModel):
    code: str

class InviteCreate(BaseModel):
    count: int = 10  # Default number of invites to generate

class InviteResponse(InviteBase):
    id: str
    is_used: bool
    created_at: datetime
    used_by_id: Optional[str] = None
    created_by_id: str

    model_config = ConfigDict(from_attributes=True) 

class InviteList(BaseModel):
    items: List[InviteResponse]
    total: int

    model_config = ConfigDict(from_attributes=True) 