"""Redis caching with graceful degradation.

All functions are safe to call when Redis is unavailable — they catch
exceptions and return sensible defaults (None / no-op).
"""

import json
import logging

import logfire
from redis.asyncio import Redis

from src.config import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None

DEFAULT_TTL = 7 * 24 * 60 * 60  # 7 days


async def init_redis() -> Redis | None:
    """Connect to Redis. Returns None on failure so the app can still run."""
    global _redis
    if not settings.redis_enabled:
        logger.info("Redis disabled (REDIS_ENABLED=false)")
        return None
    try:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
        await _redis.ping()
        logger.info("Redis connected at %s", settings.redis_url)
        return _redis
    except Exception:
        logger.warning("Redis unavailable — caching disabled", exc_info=True)
        _redis = None
        return None


async def close_redis() -> None:
    """Gracefully close the Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis | None:
    """Return the current Redis client (may be None)."""
    return _redis


@logfire.instrument("cache:get {key}")
async def cache_get(key: str) -> dict | None:
    """Get a JSON-serialised value. Returns None on miss or if Redis is down."""
    if _redis is None:
        return None
    try:
        raw = await _redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("cache_get failed for key=%s", key, exc_info=True)
        return None


@logfire.instrument("cache:set {key}")
async def cache_set(key: str, value: dict, ttl: int = DEFAULT_TTL) -> None:
    """Store a JSON-serialised value. Silent no-op when Redis is unavailable."""
    if _redis is None:
        return
    try:
        await _redis.set(key, json.dumps(value), ex=ttl)
    except Exception:
        logger.warning("cache_set failed for key=%s", key, exc_info=True)


@logfire.instrument("cache:invalidate {pattern}")
async def cache_invalidate(pattern: str) -> int:
    """Delete keys matching *pattern* via SCAN. Returns count of deleted keys."""
    if _redis is None:
        return 0
    try:
        deleted = 0
        async for key in _redis.scan_iter(match=pattern, count=100):
            await _redis.delete(key)
            deleted += 1
        return deleted
    except Exception:
        logger.warning("cache_invalidate failed for pattern=%s", pattern, exc_info=True)
        return 0
