import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.main import app
from app.api import deps
from app.core.config import settings
from app.models import User, Topic, Agent, UserRole
from app.core.security import create_access_token
# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[deps.get_db] = override_get_db
    client = TestClient(app=app)  # Initialize with keyword argument
    try:
        yield client
    finally:
        app.dependency_overrides.clear()

@pytest.fixture
def superuser_token_headers(client):
    """Return superuser token headers for testing."""
    user_id = str(uuid.uuid4())
    superuser = User(
        id=user_id,
        email="admin@example.com",
        hashed_password="hashed_admin",
        is_active=True,
        role=UserRole.ADMIN,
        full_name="Admin User"
    )
    db = TestingSessionLocal()
    db.add(superuser)
    db.commit()
    
    auth_token = create_access_token(user_id)
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def normal_user_token_headers(client):
    """Return normal user token headers for testing."""
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="user@example.com",
        hashed_password="hashed_password",
        full_name="John Doe",
        is_active=True
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    
    auth_token = create_access_token(user_id)
    return {"Authorization": f"Bearer {auth_token}"} 