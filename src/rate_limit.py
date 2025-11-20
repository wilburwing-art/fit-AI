"""Rate limiting configuration and utilities"""

import logging
from typing import Optional

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Returns user ID if authenticated, otherwise falls back to IP address.
    This allows for user-based rate limiting on authenticated endpoints
    and IP-based rate limiting on public/auth endpoints.
    """
    # Check if user is authenticated (FastAPI-Users stores user in request.state)
    user = getattr(request.state, "user", None)

    if user and hasattr(user, "id"):
        identifier = f"user:{user.id}"
        logger.debug(f"Rate limit identifier: {identifier}")
        return identifier

    # Fall back to IP address for unauthenticated requests
    ip_address = get_remote_address(request)
    logger.debug(f"Rate limit identifier (IP): {ip_address}")
    return ip_address


def get_ip_only(request: Request) -> str:
    """
    Get IP address only for rate limiting.

    Used for auth endpoints where we always want IP-based limiting
    regardless of authentication status.
    """
    ip_address = get_remote_address(request)
    logger.debug(f"Rate limit identifier (IP-only): {ip_address}")
    return ip_address


# Configure rate limiter with in-memory storage
# When Redis is available, this can be swapped to RedisStorage
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["1000/hour"],  # Default fallback limit
    headers_enabled=True,  # Include X-RateLimit-* headers in responses
    storage_uri="memory://",  # In-memory storage (no Redis required)
)


def log_rate_limit_hit(request: Request, limit: str):
    """
    Log when a rate limit is hit for monitoring/alerting.

    In production, this should trigger alerts if:
    - AI endpoints are being hit frequently (potential cost bomb)
    - Auth endpoints are being brute-forced
    """
    identifier = get_user_identifier(request)
    path = request.url.path

    logger.warning(
        f"Rate limit exceeded",
        extra={
            "identifier": identifier,
            "path": path,
            "limit": limit,
            "headers": dict(request.headers),
        }
    )

    # TODO: Send to monitoring system (Logfire, Sentry, etc.)
    # if path.startswith("/api/ai"):
    #     alert_ai_cost_risk(identifier, path)
    # elif path.startswith("/auth"):
    #     alert_security_team(identifier, path)


# Rate limit presets for different endpoint types
RATE_LIMITS = {
    # Auth endpoints (IP-based, strict to prevent brute force)
    "auth_register": "5/hour",
    "auth_login": "10/hour",
    "auth_reset_password": "3/hour",

    # AI endpoints (user-based, very strict to prevent cost bombs)
    "ai_workout_plan": "5/day",
    "ai_nutrition_plan": "5/day",

    # Data endpoints (user-based, generous for normal usage)
    "data_post": "100/hour",
    "data_get": "200/hour",
}


# List of IP addresses/CIDR ranges to exempt from rate limiting
# Useful for:
# - Health check endpoints
# - Internal services
# - Load balancer IPs
RATE_LIMIT_EXEMPT_IPS = [
    "127.0.0.1",  # Localhost
    "::1",        # IPv6 localhost
    # Add load balancer/health check IPs here
    # "10.0.0.0/8",  # Example: internal network
]


def is_exempt_from_rate_limit(request: Request) -> bool:
    """
    Check if a request should be exempt from rate limiting.

    Returns True for:
    - Health check endpoints
    - Requests from exempt IP addresses
    """
    # Exempt health check endpoint
    if request.url.path == "/health":
        return True

    # Check if IP is in exempt list
    ip_address = get_remote_address(request)
    if ip_address in RATE_LIMIT_EXEMPT_IPS:
        logger.debug(f"IP {ip_address} is exempt from rate limiting")
        return True

    return False
