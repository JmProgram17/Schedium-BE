# app/core/security/rate_limiter.py
"""
Rate limiting implementation using Redis.
Prevents API abuse and ensures fair usage.
"""

import time
from typing import Optional, Tuple

import redis
from fastapi import HTTPException, Request, status

from app.config import settings
from app.core.exceptions import RateLimitExceededException


class RateLimiter:
    """Rate limiter using Redis with sliding window algorithm."""

    def __init__(
        self,
        redis_client: redis.Redis,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting."""
        # Priority: authenticated user > API key > IP address
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _check_rate_limit(
        self, key: str, window_seconds: int, max_requests: int
    ) -> Tuple[bool, int, int]:
        """
        Check if rate limit is exceeded.

        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time)
        """
        now = time.time()
        pipeline = self.redis.pipeline()

        # Remove old entries
        pipeline.zremrangebyscore(key, 0, now - window_seconds)

        # Count current requests
        pipeline.zcard(key)

        # Add current request
        pipeline.zadd(key, {str(now): now})

        # Set expiry
        pipeline.expire(key, window_seconds + 1)

        results = pipeline.execute()
        request_count = results[1]

        if request_count >= max_requests:
            # Get oldest request time to calculate reset
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_time = int(oldest[0][1] + window_seconds)
            else:
                reset_time = int(now + window_seconds)

            return False, 0, reset_time

        remaining = max_requests - request_count - 1
        reset_time = int(now + window_seconds)

        return True, remaining, reset_time

    async def check_rate_limit(self, request: Request) -> None:
        """Check rate limits and raise exception if exceeded."""
        identifier = self._get_identifier(request)

        # Check minute limit
        minute_key = f"rate_limit:minute:{identifier}"
        minute_allowed, minute_remaining, minute_reset = self._check_rate_limit(
            minute_key, 60, self.requests_per_minute
        )

        # Check hour limit
        hour_key = f"rate_limit:hour:{identifier}"
        hour_allowed, hour_remaining, hour_reset = self._check_rate_limit(
            hour_key, 3600, self.requests_per_hour
        )

        # Add headers
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(minute_remaining),
            "X-RateLimit-Reset": str(minute_reset),
        }

        if not minute_allowed:
            raise RateLimitExceededException(
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(minute_reset),
                    "Retry-After": str(minute_reset - int(time.time())),
                },
            )

        if not hour_allowed:
            raise RateLimitExceededException(
                detail="Hourly rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                    "X-RateLimit-Remaining-Hour": "0",
                    "X-RateLimit-Reset-Hour": str(hour_reset),
                    "Retry-After": str(hour_reset - int(time.time())),
                },
            )


# Singleton instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    global _rate_limiter

    if not _rate_limiter and settings.RATE_LIMIT_ENABLED:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        _rate_limiter = RateLimiter(
            redis_client,
            settings.RATE_LIMIT_PER_MINUTE,
            settings.RATE_LIMIT_PER_HOUR,
        )

    return _rate_limiter
