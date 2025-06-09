"""
Common validators used across the application.
Provides reusable validation functions.
"""

import re
from datetime import date, datetime
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    # Remove common separators
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    # Check if it's a valid phone number (7-15 digits)
    return bool(re.match(r"^\+?\d{7,15}$", cleaned))


def validate_document_number(document: str) -> bool:
    """
    Validate Colombian document number (CC, CE, etc).

    Args:
        document: Document number to validate

    Returns:
        True if valid, False otherwise
    """
    # Remove non-alphanumeric characters
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", document)
    # Check length (6-20 characters)
    return 6 <= len(cleaned) <= 20


def validate_colombian_document(document: str) -> bool:
    """
    Validate Colombian document (CC, CE, TI, etc).
    """
    # Remove non-numeric characters for CC
    cleaned = re.sub(r"[^0-9]", "", document)

    # Colombian CC typically 6-10 digits
    if cleaned.isdigit() and 6 <= len(cleaned) <= 10:
        return True

    # CE format: letters and numbers
    if re.match(r"^[A-Z]{2}\d{6,8}$", document.upper()):
        return True

    return False


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Validate that end date is after start date.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        True if valid, False otherwise
    """
    return end_date >= start_date


def validate_time_slot(start_time: str, end_time: str) -> bool:
    """
    Validate time slot format (HH:MM).

    Args:
        start_time: Start time string
        end_time: End time string

    Returns:
        True if valid, False otherwise
    """
    time_pattern = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"

    if not (re.match(time_pattern, start_time) and re.match(time_pattern, end_time)):
        return False

    # Convert to minutes for comparison
    start_h, start_m = map(int, start_time.split(":"))
    end_h, end_m = map(int, end_time.split(":"))

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    return end_minutes > start_minutes


def validate_capacity(capacity: int) -> bool:
    """
    Validate capacity is positive.

    Args:
        capacity: Capacity value

    Returns:
        True if valid, False otherwise
    """
    return capacity > 0


def validate_hour_limit(hours: float) -> bool:
    """
    Validate hour limit is reasonable.

    Args:
        hours: Number of hours

    Returns:
        True if valid, False otherwise
    """
    return 0 < hours <= 168  # Max 168 hours per week


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    # Remove leading/trailing whitespace
    sanitized = value.strip()

    # Replace multiple spaces with single space
    sanitized = re.sub(r"\s+", " ", sanitized)

    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized
