"""
Database configuration module.
Handles SQLAlchemy engine, session management, and base model.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Database engine configuration
engine_config = {
    "pool_pre_ping": True,  # Verify connections before using
    "pool_size": 5,  # Number of connections to maintain in pool
    "max_overflow": 10,  # Maximum overflow connections allowed
    "pool_timeout": 30,  # Timeout for getting connection from pool
    "pool_recycle": 3600,  # Recycle connections after 1 hour
    "echo": settings.DEBUG,  # Log SQL statements in debug mode
    "future": True,  # Use SQLAlchemy 2.0 style
}

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    **engine_config
)

# Configure session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

# Add naming convention for constraints
Base.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Ensures proper cleanup after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database connection.
    Test connection and log status.
    """
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection established successfully")
        
        # Log connection pool status
        logger.info(f"Database pool size: {engine.pool.size()}")
        logger.info(f"Database pool checked out connections: {engine.pool.checkedout()}")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise


# Event listeners for connection pool monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log new database connections."""
    logger.debug("New database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkouts from pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection returns to pool."""
    logger.debug("Connection returned to pool")


# MySQL specific configurations
if "mysql" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_mysql_mode(dbapi_connection, connection_record):
        """Set MySQL specific modes for better compatibility."""
        cursor = dbapi_connection.cursor()
        # Enable ANSI quotes for identifier quoting
        cursor.execute("SET sql_mode = 'ANSI_QUOTES'")
        # Set timezone to UTC
        cursor.execute("SET time_zone = '+00:00'")
        # Set character set
        cursor.execute("SET NAMES 'utf8mb4'")
        cursor.close()