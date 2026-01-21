"""Main FastAPI application"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from src.api import ai_router, auth_router, data_router, pages_router
from src.config import settings
from src.database import DatabaseSession, create_db_and_tables
from src.exceptions import (
    AIServiceError,
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConflictError,
    FitAgentException,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from src.rate_limit import limiter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup: Create database tables (development only)
    if settings.debug:
        await create_db_and_tables()
    yield
    # Shutdown: Cleanup if needed


app = FastAPI(
    title="Fit Agent",
    description="AI-Powered Fitness Tracking Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="src/templates")


# Global exception handlers for custom exceptions
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error: {exc.message}", extra={"details": exc.details})
    return JSONResponse(status_code=400, content={"detail": exc.user_message})


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    logger.warning(f"Authentication error: {exc.message}")
    return JSONResponse(status_code=401, content={"detail": exc.user_message})


@app.exception_handler(AuthorizationError)
async def authz_error_handler(request: Request, exc: AuthorizationError):
    logger.warning(f"Authorization error: {exc.message}")
    return JSONResponse(status_code=403, content={"detail": exc.user_message})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.user_message})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    logger.warning(f"Conflict error: {exc.message}")
    return JSONResponse(status_code=409, content={"detail": exc.user_message})


@app.exception_handler(BusinessLogicError)
async def business_logic_handler(request: Request, exc: BusinessLogicError):
    return JSONResponse(status_code=422, content={"detail": exc.user_message})


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    logger.warning(f"Rate limit exceeded: {exc.message}")
    return JSONResponse(status_code=429, content={"detail": exc.user_message})


@app.exception_handler(AIServiceError)
async def ai_service_handler(request: Request, exc: AIServiceError):
    logger.error(f"AI service error: {exc.message}", extra={"details": exc.details})
    return JSONResponse(status_code=503, content={"detail": exc.user_message})


@app.exception_handler(FitAgentException)
async def generic_fit_agent_handler(request: Request, exc: FitAgentException):
    logger.error(
        f"Unhandled FitAgentException: {exc.message}", extra={"details": exc.details}
    )
    return JSONResponse(
        status_code=500, content={"detail": "An unexpected error occurred"}
    )


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(data_router, prefix="/api", tags=["data"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(pages_router, tags=["pages"])


@app.get("/health")
async def health_check(session: DatabaseSession):
    """Health check endpoint with database connectivity verification"""
    try:
        await session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    status = "healthy" if db_status == "healthy" else "degraded"
    return {
        "status": status,
        "environment": settings.environment,
        "database": db_status,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
