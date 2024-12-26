from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class FileBase(BaseModel):
    """Base file schema with common fields."""
    title: str = Field(..., description="Display title for the file")
    description: Optional[str] = Field(None, description="Optional description of the file contents")

class FileCreate(FileBase):
    """Schema for file creation."""
    pass

class FileUpdate(FileBase):
    """Schema for file updates."""
    title: Optional[str] = None
    description: Optional[str] = None

class FileResponse(FileBase):
    """Schema for file responses."""
    id: str
    filename: str
    file_path: str
    content_type: str
    size: int
    created_at: datetime
    topic_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) 