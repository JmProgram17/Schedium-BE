"""
Application monitoring and metrics collection.
Provides monitoring capabilities for performance, errors, and usage metrics.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from fastapi import Request, Response

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ApplicationMonitor:
    """Monitor application metrics and performance."""

    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "requests_by_status": {},
            "response_times": [],
            "errors_total": 0,
            "errors_by_type": {},
            "active_users": set(),
            "database_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self.start_time = datetime.utcnow()

    def record_request(
        self,
        request: Request,
        response: Response,
        process_time: float,
        user_id: Optional[int] = None,
    ):
        """Record request metrics."""
        # Update total requests
        self.metrics["requests_total"] += 1

        # Update endpoint metrics
        endpoint = f"{request.method} {request.url.path}"
        self.metrics["requests_by_endpoint"][endpoint] = (
            self.metrics["requests_by_endpoint"].get(endpoint, 0) + 1
        )

        # Update status code metrics
        status_code = response.status_code
        self.metrics["requests_by_status"][status_code] = (
            self.metrics["requests_by_status"].get(status_code, 0) + 1
        )

        # Record response time
        self.metrics["response_times"].append(process_time)

        # Keep only last 1000 response times for memory efficiency
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

        # Track active users
        if user_id:
            self.metrics["active_users"].add(user_id)

        # Log slow requests
        if process_time > 1.0:  # Requests taking more than 1 second
            logger.warning(
                "slow_request",
                endpoint=endpoint,
                process_time=process_time,
                status_code=status_code,
                user_id=user_id,
            )

    def record_error(self, error_type: str, details: Dict[str, Any]):
        """Record error metrics."""
        self.metrics["errors_total"] += 1
        self.metrics["errors_by_type"][error_type] = (
            self.metrics["errors_by_type"].get(error_type, 0) + 1
        )

        logger.error(
            "application_error",
            error_type=error_type,
            details=details,
            event_type="error",
        )

    def record_database_query(self):
        """Record database query execution."""
        self.metrics["database_queries"] += 1

    def record_cache_hit(self):
        """Record cache hit."""
        self.metrics["cache_hits"] += 1

    def record_cache_miss(self):
        """Record cache miss."""
        self.metrics["cache_misses"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current application metrics."""
        uptime = datetime.utcnow() - self.start_time
        uptime_seconds = uptime.total_seconds()

        # Calculate average response time
        avg_response_time = 0
        if self.metrics["response_times"]:
            avg_response_time = sum(self.metrics["response_times"]) / len(
                self.metrics["response_times"]
            )

        # Calculate requests per second
        requests_per_second = (
            self.metrics["requests_total"] / uptime_seconds if uptime_seconds > 0 else 0
        )

        # Calculate cache hit ratio
        total_cache_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_ratio = (
            self.metrics["cache_hits"] / total_cache_requests
            if total_cache_requests > 0
            else 0
        )

        return {
            "uptime_seconds": uptime_seconds,
            "requests_total": self.metrics["requests_total"],
            "requests_per_second": round(requests_per_second, 2),
            "average_response_time": round(avg_response_time, 4),
            "active_users_count": len(self.metrics["active_users"]),
            "errors_total": self.metrics["errors_total"],
            "database_queries": self.metrics["database_queries"],
            "cache_hit_ratio": round(cache_hit_ratio, 3),
            "requests_by_endpoint": dict(
                sorted(
                    self.metrics["requests_by_endpoint"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]  # Top 10 endpoints
            ),
            "requests_by_status": self.metrics["requests_by_status"],
            "errors_by_type": self.metrics["errors_by_type"],
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status."""
        metrics = self.get_metrics()

        # Determine health status based on metrics
        health_status = "healthy"
        issues = []

        # Check error rate (more than 5% in last period)
        if metrics["requests_total"] > 0:
            error_rate = metrics["errors_total"] / metrics["requests_total"]
            if error_rate > 0.05:
                health_status = "degraded"
                issues.append(f"High error rate: {error_rate:.2%}")

        # Check average response time (more than 2 seconds)
        if metrics["average_response_time"] > 2.0:
            health_status = "degraded"
            issues.append(f"Slow response time: {metrics['average_response_time']:.2f}s")

        # Check cache performance (less than 50% hit rate)
        if metrics["cache_hit_ratio"] < 0.5 and metrics["cache_hit_ratio"] > 0:
            health_status = "degraded"
            issues.append(f"Low cache hit ratio: {metrics['cache_hit_ratio']:.2%}")

        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": metrics["uptime_seconds"],
            "issues": issues,
            "metrics_summary": {
                "total_requests": metrics["requests_total"],
                "error_rate": (
                    metrics["errors_total"] / metrics["requests_total"]
                    if metrics["requests_total"] > 0
                    else 0
                ),
                "avg_response_time": metrics["average_response_time"],
                "active_users": metrics["active_users_count"],
            },
        }

    def log_periodic_metrics(self):
        """Log metrics periodically for monitoring."""
        metrics = self.get_metrics()
        health = self.get_health_status()

        logger.info(
            "periodic_metrics",
            metrics=metrics,
            health_status=health["status"],
            event_type="metrics",
        )


class PerformanceProfiler:
    """Profile performance of specific operations."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.logger = get_logger(f"profiler.{operation_name}")

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time

            # Log performance metrics
            self.logger.info(
                "operation_completed",
                operation=self.operation_name,
                duration=duration,
                success=exc_type is None,
                event_type="performance",
            )

            # Log warnings for slow operations
            if duration > 5.0:  # Operations taking more than 5 seconds
                self.logger.warning(
                    "slow_operation",
                    operation=self.operation_name,
                    duration=duration,
                    event_type="performance_warning",
                )

            # Record metrics in global monitor if available
            if hasattr(app_monitor, "record_database_query") and "database" in self.operation_name.lower():
                app_monitor.record_database_query()


class AlertManager:
    """Manage application alerts and notifications."""

    def __init__(self):
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5%
            "response_time": 2.0,  # 2 seconds
            "memory_usage": 0.85,  # 85%
            "disk_usage": 0.90,  # 90%
        }
        self.alerts_sent = {}

    def check_and_send_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and send alerts if needed."""
        current_time = datetime.utcnow()

        # Check error rate
        if metrics["requests_total"] > 0:
            error_rate = metrics["errors_total"] / metrics["requests_total"]
            if error_rate > self.alert_thresholds["error_rate"]:
                self._send_alert(
                    "high_error_rate",
                    f"Error rate is {error_rate:.2%}, threshold: {self.alert_thresholds['error_rate']:.2%}",
                    current_time,
                )

        # Check response time
        if metrics["average_response_time"] > self.alert_thresholds["response_time"]:
            self._send_alert(
                "slow_response_time",
                f"Average response time is {metrics['average_response_time']:.2f}s, threshold: {self.alert_thresholds['response_time']}s",
                current_time,
            )

    def _send_alert(self, alert_type: str, message: str, timestamp: datetime):
        """Send an alert (placeholder for actual notification system)."""
        # Check if we've already sent this alert recently (within 5 minutes)
        if alert_type in self.alerts_sent:
            last_sent = self.alerts_sent[alert_type]
            if timestamp - last_sent < timedelta(minutes=5):
                return  # Don't spam alerts

        # Log the alert
        logger.error(
            "application_alert",
            alert_type=alert_type,
            message=message,
            timestamp=timestamp.isoformat(),
            event_type="alert",
        )

        # Record when we sent this alert
        self.alerts_sent[alert_type] = timestamp

        # In a real implementation, you would:
        # - Send email notifications
        # - Send Slack/Discord messages
        # - Create incidents in monitoring systems
        # - Send SMS for critical alerts


# Global instances
app_monitor = ApplicationMonitor()
alert_manager = AlertManager()


def profile_operation(operation_name: str):
    """Decorator to profile operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceProfiler(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def get_monitoring_data() -> Dict[str, Any]:
    """Get comprehensive monitoring data."""
    metrics = app_monitor.get_metrics()
    health = app_monitor.get_health_status()

    return {
        "metrics": metrics,
        "health": health,
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }