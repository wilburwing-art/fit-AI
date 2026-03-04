"""E2E test infrastructure: live server, browser helpers, fixtures."""

import os
import tempfile
import threading
import time
from collections.abc import AsyncGenerator
from uuid import uuid4

import httpx
import pytest
import uvicorn
from fastapi_users.password import PasswordHelper
from playwright.sync_api import Page
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

from src.config import settings
from src.database import get_async_session
from src.main import app
from src.models import User

E2E_PORT = 8765
BASE_URL = f"http://127.0.0.1:{E2E_PORT}"

# File-based SQLite so the uvicorn server and test fixtures share data
_db_file = os.path.join(tempfile.gettempdir(), f"test_e2e_{os.getpid()}.db")
E2E_DATABASE_URL_ASYNC = f"sqlite+aiosqlite:///{_db_file}"
E2E_DATABASE_URL_SYNC = f"sqlite:///{_db_file}"

# Async engine for the server's dependency override
_async_engine = create_async_engine(E2E_DATABASE_URL_ASYNC, echo=False, future=True)
_async_session_maker = async_sessionmaker(
    _async_engine, class_=AsyncSession, expire_on_commit=False
)

# Sync engine for test fixture DB operations (avoids event loop conflicts)
_sync_engine = create_engine(E2E_DATABASE_URL_SYNC, echo=False, future=True)
_sync_session_maker = sessionmaker(_sync_engine, class_=Session, expire_on_commit=False)


@pytest.fixture(scope="session")
def live_server():
    """Start a real uvicorn server in a background thread (session-scoped)."""
    # Create tables using sync engine
    SQLModel.metadata.create_all(_sync_engine)

    # Override DB dependency to use the file-based async engine
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with _async_session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_db

    settings.environment = "test"
    settings.debug = False

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=E2E_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to be ready
    for _ in range(50):
        try:
            resp = httpx.get(f"{BASE_URL}/health")
            if resp.status_code == 200:
                break
        except httpx.ConnectError:
            pass
        time.sleep(0.1)
    else:
        raise RuntimeError("E2E server did not start in time")

    yield BASE_URL

    server.should_exit = True
    thread.join(timeout=5)
    app.dependency_overrides.clear()

    # Cleanup
    SQLModel.metadata.drop_all(_sync_engine)
    _sync_engine.dispose()
    if os.path.exists(_db_file):
        os.unlink(_db_file)


@pytest.fixture
def registered_user(live_server):
    """Create a user directly in the DB using sync engine."""
    email = f"e2e_{uuid4().hex[:8]}@test.com"
    password = "e2eTestPass123!"

    pw_helper = PasswordHelper()
    hashed = pw_helper.hash(password)

    user_id = uuid4()
    user = User(
        id=user_id,
        email=email,
        hashed_password=hashed,
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    with _sync_session_maker() as session:
        session.add(user)
        session.commit()
        session.refresh(user)

    yield {"email": email, "password": password, "user": user}

    # Cleanup
    with _sync_session_maker() as session:
        db_user = session.get(User, user_id)
        if db_user:
            session.delete(db_user)
            session.commit()


def login_via_browser(page: Page, base_url: str, email: str, password: str):
    """Log in through the browser UI (sync Playwright API)."""
    page.goto(f"{base_url}/login")
    page.fill("#username", email)
    page.fill("#password", password)
    page.click('button[type="submit"]')
    # The login form uses HTMX + JS redirect: window.location.href = '/dashboard'
    page.wait_for_url("**/dashboard", timeout=10000)


@pytest.fixture
def authenticated_page(page: Page, live_server: str, registered_user: dict):
    """A Playwright page already logged in."""
    login_via_browser(
        page, live_server, registered_user["email"], registered_user["password"]
    )
    yield page
