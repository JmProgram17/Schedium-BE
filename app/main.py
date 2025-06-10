"""
Main application module.
Configures FastAPI app with middleware, routes, and event handlers.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api.v1.router import api_router
from app.config import settings
from app.core.auth_middleware import AuthenticationMiddleware
from app.database import init_db
from app.core.middleware import (
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
)
from app.core.middleware.security import SecurityMiddleware
from app.core.security.cors import configure_cors
from app.core.security.headers import SecurityHeadersMiddleware
from app.core.logging import setup_logging, get_logger

# Configure logging first
setup_logging()
logger = get_logger(__name__)

# Create app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
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

# 7. Authentication (last, uses request state)
app.add_middleware(AuthenticationMiddleware)

# 8. Add trusted host check for production
if settings.IS_PRODUCTION:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


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
    # Security configurations
    swagger_ui_parameters={
        "persistAuthorization": True,
        "filter": True,
    } if not settings.IS_PRODUCTION else None,
)

# Configure CORS with security
configure_cors(app)

# Add security middlewares in order
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(AuthenticationMiddleware)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
    if settings.IS_DEVELOPMENT
    else [
        origin.replace("http://", "").replace("https://", "")
        for origin in settings.BACKEND_CORS_ORIGINS
    ],
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


# Add request ID middleware
@app.middleware("http")
async def add_request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add unique request ID for tracking."""
    import uuid

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint returning API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": f"{settings.API_V1_STR}/docs" if not settings.IS_PRODUCTION else None,
        "health": "/health",
    }


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns application and database status.
    """
    from sqlalchemy import text

    from app.database import engine

    health_status = {
        "status": "healthy",
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        },
    }

    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = {"status": "connected"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = {"status": "disconnected", "error": str(e)}

    return health_status


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if settings.IS_PRODUCTION else str(exc),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)
