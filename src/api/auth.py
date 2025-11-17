"""Authentication routes"""

from fastapi import APIRouter

from src.auth import auth_backend, fastapi_users
from src.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter()

# Include FastAPI-Users auth routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
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
