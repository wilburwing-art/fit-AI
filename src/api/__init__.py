"""API routes"""

from src.api.ai import router as ai_router
from src.api.auth import router as auth_router
from src.api.data import router as data_router
from src.api.pages import router as pages_router

__all__ = ["ai_router", "auth_router", "data_router", "pages_router"]
