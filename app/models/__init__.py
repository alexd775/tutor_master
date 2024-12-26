# Import all models here to make them available at the package level
from app.models.user import User, UserRole, UserPreference
from app.models.topic import Topic
from app.models.session import Session
from app.models.analytics import UserAnalytics, TopicAnalytics, SessionAnalytics
from app.models.file import File
from app.models.agent import Agent, AgentType
from app.models.chat import ChatMessage, MessageRole

# This allows other modules to import directly from app.models
__all__ = [
    "User",
    "UserRole",
    "UserPreference",
    "Topic",
    "Session",
    "UserAnalytics",
    "TopicAnalytics",
    "SessionAnalytics",
    "File",
    "Agent",
    "AgentType",
    "ChatMessage",
    "MessageRole",
]
