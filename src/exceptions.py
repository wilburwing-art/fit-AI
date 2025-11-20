"""Custom exception classes for structured error handling"""

from typing import Any


class FitAgentException(Exception):
    """Base exception for all Fit Agent errors"""

    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Args:
            message: Technical error message for logging
            user_message: User-friendly message to display (defaults to message)
            details: Additional context for debugging
        """
        self.message = message
        self.user_message = user_message or message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(FitAgentException):
    """Invalid data provided by user (400)"""

    pass


class AuthenticationError(FitAgentException):
    """Authentication failed (401)"""

    pass


class AuthorizationError(FitAgentException):
    """User lacks permission (403)"""

    pass


class NotFoundError(FitAgentException):
    """Resource not found (404)"""

    pass


class ConflictError(FitAgentException):
    """Resource conflict (e.g., duplicate entry) (409)"""

    pass


class BusinessLogicError(FitAgentException):
    """Business rule violation (422)"""

    pass


class AIServiceError(FitAgentException):
    """AI service failure (503)"""

    pass


class ExternalServiceError(FitAgentException):
    """External service unavailable (503)"""

    pass


class RateLimitError(FitAgentException):
    """Rate limit exceeded (429)"""

    pass
