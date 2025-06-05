"""
Main application module.
Configures FastAPI app with middleware, routes, and event handlers.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    lifespan=lifespan
)

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.IS_DEVELOPMENT else [origin.replace("http://", "").replace("https://", "") for origin in settings.BACKEND_CORS_ORIGINS]
)


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracking."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": f"{settings.API_V1_STR}/docs" if not settings.IS_PRODUCTION else None,
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns application and database status.
    """
    from app.database import engine
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        }
    }
    
    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = {"status": "connected"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = {
            "status": "disconnected",
            "error": str(e)
        }
    
    return health_status


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if settings.IS_PRODUCTION else str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Include API routers
from app.api.v1.router import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)