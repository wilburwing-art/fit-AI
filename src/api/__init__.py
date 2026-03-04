"""API routes"""

from src.api.ai import router as ai_router
from src.api.analytics import router as analytics_router
from src.api.auth import router as auth_router
from src.api.data import router as data_router
from src.api.exercises import router as exercises_router
from src.api.export import router as export_router
from src.api.pages import router as pages_router

__all__ = [
    "ai_router",
    "analytics_router",
    "auth_router",
    "data_router",
    "exercises_router",
    "export_router",
    "pages_router",
]
