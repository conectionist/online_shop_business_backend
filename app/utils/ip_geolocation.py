"""IP geolocation utility for session management.

This module provides functionality to resolve IP addresses to approximate
geographic locations. Currently implemented as a stub for MVP.

Future enhancements could include:
- MaxMind GeoLite2 database integration (offline, privacy-friendly)
- External API integration (ipapi.co, ip-api.com)
"""

from typing import Optional, Dict


def get_location_from_ip(ip_address: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Get approximate location from IP address.
    
    Args:
        ip_address: IP address to geolocate
        
    Returns:
        Dictionary with keys: city, country
        
    Note:
        This is a stub implementation for MVP. Returns None for both fields.
        Future implementations could use GeoLite2 database or external APIs.
        
    Example:
        >>> get_location_from_ip("8.8.8.8")
        {"city": None, "country": None}
    """
    # For MVP, return None for both fields
    # This avoids external dependencies and privacy concerns
    return {
        "city": None,
        "country": None
    }


def is_geolocation_available() -> bool:
    """
    Check if geolocation functionality is available.
    
    Returns:
        False for stub implementation, True when real implementation is added
    """
    return False
