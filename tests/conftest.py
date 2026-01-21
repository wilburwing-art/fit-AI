"""Pytest configuration and shared fixtures"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.config import settings
from src.database import get_async_session
from src.main import app
from src.models import User, UserProfile


# Override database URL for tests - use in-memory SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for the test session"""
    return asyncio.get_event_loop_policy()


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_maker(test_engine):
    """Create test session maker"""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_db(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with automatic rollback.

    Each test gets a fresh database session that rolls back after completion,
    ensuring test isolation.
    """
    async with test_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with overridden database dependency.

    This ensures all API calls use the test database.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """
    Create a test user for authentication tests.

    Returns an active, verified user with known credentials.
    """
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("testpassword123")

    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_user_profile(test_db: AsyncSession, test_user: User) -> UserProfile:
    """Create a test user profile"""
    profile = UserProfile(
        user_id=test_user.id,
        age=30,
        sex="M",
        experience_level="intermediate",
        equipment_access=["barbell", "dumbbells", "bench"],
        injuries=None,
        time_availability=300,
        preferences={"goal": "muscle_gain"},
    )

    test_db.add(profile)
    await test_db.commit()
    await test_db.refresh(profile)

    return profile


@pytest_asyncio.fixture
async def authenticated_client(
    test_client: AsyncClient,
    test_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create authenticated test client with JWT token.

    Automatically logs in test_user and includes JWT in headers.
    """
    # Login to get JWT token
    login_response = await test_client.post(
        "/auth/jwt/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )

    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data["access_token"]

    # Add token to client headers
    test_client.headers["Authorization"] = f"Bearer {access_token}"

    yield test_client

    # Clean up
    test_client.headers.pop("Authorization", None)


@pytest_asyncio.fixture
async def second_test_user(test_db: AsyncSession) -> User:
    """Create a second test user for multi-user tests"""
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("testpassword456")

    user = User(
        id=uuid4(),
        email="test2@example.com",
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    return user


@pytest.fixture
def mock_ai_response_workout():
    """Mock successful workout plan AI response"""
    return {
        "weeks": 8,
        "phases": [
            {
                "phase": 1,
                "weeks": 4,
                "focus": "Base building",
                "workouts_per_week": 3,
            },
            {
                "phase": 2,
                "weeks": 4,
                "focus": "Hypertrophy",
                "workouts_per_week": 4,
            },
        ],
        "exercises": [
            "Barbell Squat",
            "Bench Press",
            "Deadlift",
            "Overhead Press",
            "Barbell Row",
        ],
        "frequency": 4,
        "rationale": "Progressive overload focused program for intermediate lifter with muscle gain goals.",
    }


@pytest.fixture
def mock_ai_response_nutrition():
    """Mock successful nutrition plan AI response"""
    return {
        "daily_protein_g": 180,
        "daily_carbs_g": 250,
        "daily_fat_g": 70,
        "daily_calories": 2500,
        "meal_suggestions": [
            "Chicken breast with rice and vegetables",
            "Greek yogurt with berries and granola",
            "Salmon with sweet potato",
        ],
        "rationale": "Moderate surplus for muscle gain at 180lbs bodyweight with active lifestyle.",
    }


@pytest.fixture
def mock_pydantic_ai_agent(mocker, mock_ai_response_workout):
    """
    Mock PydanticAI Agent to avoid real API calls during tests.

    Usage:
        mock_agent = mock_pydantic_ai_agent(mocker, custom_response)
    """

    class MockResult:
        def __init__(self, data):
            self.data = data
            self.usage = type(
                "obj",
                (object,),
                {
                    "total_tokens": 1000,
                    "input_tokens": 500,
                    "output_tokens": 500,
                },
            )

    async def mock_run(*args, **kwargs):
        return MockResult(mock_ai_response_workout)

    mock_agent = mocker.MagicMock()
    mock_agent.run = mock_run

    return mock_agent


@pytest.fixture
def sample_weight_log_data():
    """Sample weight log data for testing"""
    return {
        "date": datetime.utcnow().isoformat(),
        "weight_lbs": 185.5,
        "body_fat_pct": 15.2,
        "measurements": {
            "chest": 42.0,
            "waist": 32.5,
            "arms": 15.5,
        },
    }


@pytest.fixture
def sample_meal_log_data():
    """Sample meal log data for testing"""
    return {
        "date": datetime.utcnow().isoformat(),
        "meal_type": "lunch",
        "description": "Grilled chicken with rice and vegetables",
        "protein_g": 45.0,
        "carbs_g": 60.0,
        "fat_g": 12.0,
        "calories": 540,
    }


@pytest.fixture
def sample_workout_session_data():
    """Sample workout session data for testing"""
    return {
        "scheduled_date": datetime.utcnow().isoformat(),
        "completed_date": datetime.utcnow().isoformat(),
        "duration_minutes": 75,
        "overall_rpe": 8,
        "notes": "Great session, felt strong on squats",
    }


@pytest.fixture
def sample_workout_plan_request():
    """Sample workout plan request data"""
    return {
        "user_goals": "build muscle and increase strength",
        "experience_level": "intermediate",
        "equipment_access": ["barbell", "dumbbells", "bench", "squat rack"],
        "time_availability": 300,
        "injuries": None,
        "age": 30,
    }


@pytest.fixture
def sample_nutrition_plan_request():
    """Sample nutrition plan request data"""
    return {
        "user_goals": "gain muscle while minimizing fat gain",
        "weight_lbs": 180.0,
        "activity_level": "active",
        "dietary_preferences": "no dairy",
    }


@pytest.fixture
def freeze_time():
    """Fixture to freeze time for consistent datetime testing"""
    from freezegun import freeze_time

    frozen_time = datetime(2025, 1, 15, 12, 0, 0)
    with freeze_time(frozen_time):
        yield frozen_time


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings to test values before each test"""
    settings.database_url = TEST_DATABASE_URL
    settings.environment = "test"
    settings.debug = False
    yield
    # Reset after test if needed


@pytest.fixture
def anyio_backend():
    """Configure anyio backend for pytest-asyncio"""
    return "asyncio"
