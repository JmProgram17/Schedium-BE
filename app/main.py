"""
FastAPI application entry point.
Configures middleware, routes, and application lifecycle.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware.error_handler import ErrorHandlerMiddleware
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.middleware.security import SecurityMiddleware
from app.core.security.cors import configure_cors
from app.core.security.headers import SecurityHeadersMiddleware
from app.database import init_db

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle.
    Run startup and shutdown tasks.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Initialize database
    init_db()

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if not settings.IS_PRODUCTION else None,
    docs_url=f"{settings.API_V1_STR}/docs" if not settings.IS_PRODUCTION else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if not settings.IS_PRODUCTION else None,
    lifespan=lifespan,
    debug=settings.DEBUG,
    # Security configurations
    swagger_ui_parameters={
        "persistAuthorization": True,
        "filter": True,
    } if not settings.IS_PRODUCTION else None,
)

# Middleware order is important!
# 1. Request ID (needed by other middlewares)
app.add_middleware(RequestIDMiddleware)

# 2. Error handler (catches all exceptions)
ErrorHandlerMiddleware(app)

# 3. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. CORS
configure_cors(app)

# 5. Logging (logs all requests)
app.add_middleware(LoggingMiddleware)

# 6. Security (rate limiting, validation)
app.add_middleware(SecurityMiddleware)

# 7. Add trusted host check for production
if settings.IS_PRODUCTION:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add request processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns the current status of the API.
    """
    return {
        "status": "healthy",
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        },
        "database": {"status": "connected"},
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    Returns basic API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs_url": f"{settings.API_V1_STR}/docs" if not settings.IS_PRODUCTION else None,
        "redoc_url": f"{settings.API_V1_STR}/redoc" if not settings.IS_PRODUCTION else None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )