# Import all models here for Alembic autogenerate support
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.topic import Topic  # noqa
from app.models.session import Session  # noqa
from app.models.analytics import UserAnalytics, TopicAnalytics, SessionAnalytics  # noqa 