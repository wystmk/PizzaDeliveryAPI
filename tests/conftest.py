from collections.abc import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from sqlalchemy.orm import Session
from models import User
from passlib.context import CryptContext
from database import get_db, Base, engine
from typing import Generator

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture(scope="module")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an **asynchronous** test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="module")
def db() -> Generator[Session, None, None]:
    """Provides a database session for testing."""
    Base.metadata.create_all(bind=engine)  # ✅ Ensure tables exist before tests

    session = next(get_db())  # ✅ Get a fresh session
    try:
        yield session  # ✅ Provide the session to tests
    finally:
        session.close()  # ✅ Close session

@pytest.fixture
def test_user(db: Session):
    """Create a test user and add them to the test database."""
    hashed_password = pwd_context.hash("password123")

    user = User(
        username="testuser",
        email="testuser@example.com",
        password=hashed_password,
        is_staff=True  # ✅ Make this user a staff member
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user