"""Authentication routes"""

from fastapi import APIRouter

from src.auth import auth_backend, cookie_auth_backend, fastapi_users
from src.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter()

# Include FastAPI-Users auth routes (Bearer JWT for API)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
)

# Cookie-based auth for HTML pages
router.include_router(
    fastapi_users.get_auth_router(cookie_auth_backend),
    prefix="/cookie",
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)

router.include_router(
    fastapi_users.get_reset_password_router(),
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
)
