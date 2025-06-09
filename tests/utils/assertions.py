"""
Custom assertions for testing.
"""

from typing import Any, Dict, List


def assert_valid_uuid(value: str) -> None:
    """Assert that value is a valid UUID."""
    import uuid

    try:
        uuid.UUID(value)
    except ValueError:
        raise AssertionError(f"{value} is not a valid UUID")


def assert_datetime_format(value: str, format: str = "%Y-%m-%dT%H:%M:%S") -> None:
    """Assert that value is a valid datetime string."""
    from datetime import datetime

    try:
        datetime.strptime(value, format)
    except ValueError:
        raise AssertionError(f"{value} is not a valid datetime with format {format}")


def assert_dict_subset(subset: Dict[str, Any], superset: Dict[str, Any]) -> None:
    """Assert that all items in subset exist in superset with same values."""
    for key, value in subset.items():
        assert key in superset, f"Key '{key}' not found in superset"
        assert (
            superset[key] == value
        ), f"Value mismatch for key '{key}': {superset[key]} != {value}"


def assert_response_success(response) -> None:
    """Assert that API response indicates success."""
    assert (
        response.status_code < 400
    ), f"Response failed with status {response.status_code}"

    data = response.json()
    if "success" in data:
        assert data["success"] is True, f"Response success=False: {data.get('message')}"


def assert_pagination_response(data: Dict[str, Any]) -> None:
    """Assert that response has valid pagination structure."""
    required_fields = [
        "items",
        "total",
        "page",
        "page_size",
        "total_pages",
        "has_next",
        "has_prev",
    ]

    for field in required_fields:
        assert field in data, f"Pagination field '{field}' missing"

    assert isinstance(data["items"], list), "Items must be a list"
    assert data["total"] >= 0, "Total must be non-negative"
    assert data["page"] > 0, "Page must be positive"
    assert data["page_size"] > 0, "Page size must be positive"
