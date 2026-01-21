"""Authentication setup with FastAPI-Users"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_async_session
from src.models.user import User

logger = logging.getLogger(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """User manager for FastAPI-Users"""

    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Callback after user registration"""
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Callback after forgot password request"""
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Callback after verification request"""
        logger.info(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Dependency to get user database"""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Dependency to get user manager"""
    yield UserManager(user_db)


# JWT authentication backends
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
cookie_transport = CookieTransport(
    cookie_max_age=3600 * 24 * 7, cookie_secure=not settings.debug
)


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for authentication"""
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=3600 * 24 * 7)


# Bearer backend for API calls
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Cookie backend for HTML page authentication
cookie_auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI-Users instance with both backends
fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend, cookie_auth_backend],
)

# Dependency to get current active user (raises 401 if not authenticated)
current_active_user = fastapi_users.current_user(active=True)

# Optional user dependency (returns None if not authenticated)
current_user_optional = fastapi_users.current_user(active=True, optional=True)
