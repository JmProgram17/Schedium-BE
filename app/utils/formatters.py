"""
Utility functions for formatting data.
Provides common formatters for dates, currency, phone numbers, etc.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional, Union

import re


def format_date(date_value: Union[date, datetime, str, None], format_str: str = "%Y-%m-%d") -> Optional[str]:
    """
    Format a date value to string.
    
    Args:
        date_value: Date to format (date, datetime, or ISO string)
        format_str: Format string (default: "%Y-%m-%d")
        
    Returns:
        Formatted date string or None if input is None
        
    Examples:
        >>> format_date(date(2023, 12, 25))
        '2023-12-25'
        >>> format_date(date(2023, 12, 25), "%d/%m/%Y")
        '25/12/2023'
    """
    if date_value is None:
        return None
        
    if isinstance(date_value, str):
        try:
            # Try to parse ISO format first
            if 'T' in date_value:
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            else:
                date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            return None
            
    if isinstance(date_value, datetime):
        return date_value.strftime(format_str)
    elif isinstance(date_value, date):
        return date_value.strftime(format_str)
        
    return None


def format_time(time_value: Union[time, datetime, str, None], format_str: str = "%H:%M") -> Optional[str]:
    """
    Format a time value to string.
    
    Args:
        time_value: Time to format (time, datetime, or string)
        format_str: Format string (default: "%H:%M")
        
    Returns:
        Formatted time string or None if input is None
        
    Examples:
        >>> format_time(time(14, 30))
        '14:30'
        >>> format_time(time(14, 30, 45), "%H:%M:%S")
        '14:30:45'
    """
    if time_value is None:
        return None
        
    if isinstance(time_value, str):
        try:
            # Try to parse common time formats
            if ':' in time_value:
                parts = time_value.split(':')
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    time_value = time(hour, minute, second)
                else:
                    return None
            else:
                return None
        except (ValueError, TypeError):
            return None
            
    if isinstance(time_value, datetime):
        return time_value.strftime(format_str)
    elif isinstance(time_value, time):
        return time_value.strftime(format_str)
        
    return None


def format_currency(
    amount: Union[float, int, Decimal, str, None], 
    currency: str = "COP", 
    include_symbol: bool = True
) -> Optional[str]:
    """
    Format a currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code (default: "COP" for Colombian Peso)
        include_symbol: Whether to include currency symbol
        
    Returns:
        Formatted currency string or None if input is None
        
    Examples:
        >>> format_currency(1234567.89)
        '$1,234,567.89 COP'
        >>> format_currency(1234567.89, include_symbol=False)
        '1,234,567.89 COP'
    """
    if amount is None:
        return None
        
    try:
        if isinstance(amount, str):
            amount = float(amount)
        elif isinstance(amount, Decimal):
            amount = float(amount)
            
        # Format with thousand separators
        formatted = f"{amount:,.2f}"
        
        if include_symbol:
            symbol = "$" if currency in ["COP", "USD", "MXN", "CAD", "AUD"] else ""
            return f"{symbol}{formatted} {currency}"
        else:
            return f"{formatted} {currency}"
            
    except (ValueError, TypeError):
        return None


def format_percentage(value: Union[float, int, str, None], decimal_places: int = 1) -> Optional[str]:
    """
    Format a percentage value.
    
    Args:
        value: Value to format (should be between 0-100 or 0-1)
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string or None if input is None
        
    Examples:
        >>> format_percentage(85.5)
        '85.5%'
        >>> format_percentage(0.855)
        '85.5%'
    """
    if value is None:
        return None
        
    try:
        if isinstance(value, str):
            value = float(value)
            
        # If value is between 0 and 1, assume it's a decimal percentage
        if 0 <= value <= 1:
            value = value * 100
            
        return f"{value:.{decimal_places}f}%"
        
    except (ValueError, TypeError):
        return None


def format_phone_number(phone: Optional[str], country_code: str = "CO") -> Optional[str]:
    """
    Format a phone number according to country standards.
    
    Args:
        phone: Phone number to format
        country_code: Country code (default: "CO" for Colombia)
        
    Returns:
        Formatted phone number string or None if input is None
        
    Examples:
        >>> format_phone_number("3001234567")
        '+57 300 123 4567'
        >>> format_phone_number("3001234567", "US")
        '+1 (300) 123-4567'
    """
    if not phone:
        return None
        
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    if not digits_only:
        return None
        
    if country_code == "CO":
        # Colombian format
        if len(digits_only) == 10:
            # Mobile: +57 300 123 4567
            return f"+57 {digits_only[:3]} {digits_only[3:6]} {digits_only[6:]}"
        elif len(digits_only) == 7:
            # Landline: +57 1 234 5678 (assuming Bogotá area code)
            return f"+57 1 {digits_only[:3]} {digits_only[3:]}"
    elif country_code == "US":
        # US format
        if len(digits_only) == 10:
            return f"+1 ({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif country_code == "MX":
        # Mexican format
        if len(digits_only) == 10:
            return f"+52 {digits_only[:3]} {digits_only[3:6]} {digits_only[6:]}"
            
    # Default international format
    if len(digits_only) >= 7:
        return f"+{digits_only}"
        
    return phone


def format_document_number(doc_number: Optional[str], doc_type: str = "CC") -> Optional[str]:
    """
    Format a document number according to type.
    
    Args:
        doc_number: Document number to format
        doc_type: Document type (CC, TI, CE, NIT, etc.)
        
    Returns:
        Formatted document number or None if input is None
        
    Examples:
        >>> format_document_number("1234567890")
        '1.234.567.890'
        >>> format_document_number("123456789", "NIT")
        '123.456.789'
    """
    if not doc_number:
        return None
        
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', doc_number)
    
    if not digits_only:
        return None
        
    # Add thousand separators with dots (Colombian format)
    if len(digits_only) >= 4:
        # Reverse the string, add dots every 3 digits, then reverse back
        reversed_digits = digits_only[::-1]
        formatted = '.'.join([reversed_digits[i:i+3] for i in range(0, len(reversed_digits), 3)])
        return formatted[::-1]
    
    return digits_only


def format_file_size(size_bytes: Union[int, float, None]) -> Optional[str]:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string or None if input is None
        
    Examples:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    if size_bytes is None:
        return None
        
    try:
        size_bytes = float(size_bytes)
        
        if size_bytes == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}"
        
    except (ValueError, TypeError):
        return None


def format_duration(seconds: Union[int, float, None]) -> Optional[str]:
    """
    Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string or None if input is None
        
    Examples:
        >>> format_duration(3661)
        '1h 1m 1s'
        >>> format_duration(90)
        '1m 30s'
    """
    if seconds is None:
        return None
        
    try:
        seconds = int(seconds)
        
        if seconds == 0:
            return "0s"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:  # Show seconds if it's the only unit
            parts.append(f"{secs}s")
            
        return " ".join(parts)
        
    except (ValueError, TypeError):
        return None


def format_name(first_name: Optional[str], last_name: Optional[str] = None) -> Optional[str]:
    """
    Format a person's name.
    
    Args:
        first_name: First name
        last_name: Last name (optional)
        
    Returns:
        Formatted name or None if both inputs are None
        
    Examples:
        >>> format_name("Juan", "Pérez")
        'Juan Pérez'
        >>> format_name("María")
        'María'
    """
    if not first_name and not last_name:
        return None
        
    parts = []
    if first_name:
        parts.append(first_name.strip())
    if last_name:
        parts.append(last_name.strip())
        
    return " ".join(parts) if parts else None


def format_capacity(current: Union[int, None], total: Union[int, None]) -> Optional[str]:
    """
    Format capacity as "current/total" with percentage.
    
    Args:
        current: Current usage
        total: Total capacity
        
    Returns:
        Formatted capacity string or None if inputs are None
        
    Examples:
        >>> format_capacity(25, 30)
        '25/30 (83.3%)'
        >>> format_capacity(0, 40)
        '0/40 (0.0%)'
    """
    if current is None or total is None:
        return None
        
    try:
        if total == 0:
            return f"{current}/0 (N/A)"
            
        percentage = (current / total) * 100
        return f"{current}/{total} ({percentage:.1f}%)"
        
    except (ValueError, TypeError, ZeroDivisionError):
        return None