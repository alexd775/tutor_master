from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import base, user, topic, session, analytics  # noqa: F401

# Import all models here for Alembic to detect them 