from datetime import datetime, UTC
from sqlalchemy import Column, DateTime
from app.db.base_class import Base

class BaseModel(Base):
    """Base class for all models with common fields."""
    
    __abstract__ = True

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)) 