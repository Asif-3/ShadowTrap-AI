"""
ShadowTrap AI - Validators Utility
====================================
Input validation functions for API request data.
"""

import re
from datetime import datetime


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email: Email string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email.strip()):
        return False, "Invalid email format"
    
    return True, None


def validate_password(password):
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, None


def validate_ip(ip):
    """
    Validate IPv4 address format.
    
    Args:
        ip: IP address string
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not ip or not isinstance(ip, str):
        return False, "IP address is required"
    
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip.strip()):
        return False, "Invalid IPv4 address format"
    
    # Validate each octet is 0-255
    octets = ip.strip().split('.')
    for octet in octets:
        if int(octet) > 255:
            return False, "Invalid IPv4 address: octet out of range"
    
    return True, None


def validate_session_id(session_id):
    """
    Validate session ID format (Cowrie format: hex string).
    
    Args:
        session_id: Session ID string
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not session_id or not isinstance(session_id, str):
        return False, "Session ID is required"
    
    if len(session_id) < 4:
        return False, "Session ID is too short"
    
    return True, None


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in the data dict.
    
    Args:
        data: Dictionary of input data
        required_fields: List of required field names
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not data or not isinstance(data, dict):
        return False, "Request body is required"
    
    missing = [f for f in required_fields if f not in data or not data[f]]
    
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    
    return True, None


def validate_date_range(start_date, end_date):
    """
    Validate date range for analytics queries.
    
    Args:
        start_date: Start date string (ISO format)
        end_date: End date string (ISO format)
        
    Returns:
        tuple: (is_valid, parsed_start, parsed_end, error_message)
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        if start and end and start > end:
            return False, None, None, "Start date must be before end date"
        
        return True, start, end, None
    except ValueError:
        return False, None, None, "Invalid date format. Use ISO format (YYYY-MM-DD)"


def validate_report_format(fmt):
    """
    Validate report format.
    
    Args:
        fmt: Report format string
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid_formats = ["pdf", "html", "json"]
    if fmt not in valid_formats:
        return False, f"Invalid format. Must be one of: {', '.join(valid_formats)}"
    return True, None
