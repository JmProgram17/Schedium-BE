# app/core/logging.py
"""
Enhanced logging configuration.
Structured logging with security context.
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger

from app.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""

    # Configure JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )

    # Configure handlers
    if settings.LOG_FORMAT == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(json_formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Logging context manager for adding context
class LogContext:
    """Context manager for adding logging context."""

    def __init__(self, logger: structlog.BoundLogger, **kwargs: Any) -> None:
        self.logger = logger
        self.context = kwargs

    def __enter__(self) -> structlog.BoundLogger:
        self.logger = self.logger.bind(**self.context)
        return self.logger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self.logger.exception("Exception in context", exc_info=(exc_type, exc_val, exc_tb))
        self.logger = self.logger.unbind(*self.context.keys())


# Security event logger
class SecurityLogger:
    """Specialized logger for security events."""

    def __init__(self):
        self.logger = get_logger("security")

    def log_authentication_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log authentication attempt."""
        self.logger.info(
            "authentication_attempt",
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            event_type="auth_attempt",
        )

    def log_authorization_failure(
        self,
        user_id: int,
        resource: str,
        action: str,
        required_role: Optional[str] = None,
    ) -> None:
        """Log authorization failure."""
        self.logger.warning(
            "authorization_failure",
            user_id=user_id,
            resource=resource,
            action=action,
            required_role=required_role,
            event_type="auth_failure",
        )

    def log_suspicious_activity(
        self,
        description: str,
        ip_address: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log suspicious activity."""
        self.logger.warning(
            "suspicious_activity",
            description=description,
            ip_address=ip_address,
            user_id=user_id,
            details=details or {},
            event_type="suspicious",
        )

    def log_security_violation(
        self,
        violation_type: str,
        details: Dict[str, Any],
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log security violation."""
        self.logger.error(
            "security_violation",
            violation_type=violation_type,
            details=details,
            user_id=user_id,
            ip_address=ip_address,
            event_type="violation",
        )


# Global security logger instance
security_logger = SecurityLogger()
