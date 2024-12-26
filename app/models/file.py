from sqlalchemy import Column, String, Integer, ForeignKey, Text
from app.models.base import BaseModel

class File(BaseModel):
    """File model for storing file metadata."""
    
    __tablename__ = "files"
    
    id = Column(String(36), primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String)
    size = Column(Integer)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True) 