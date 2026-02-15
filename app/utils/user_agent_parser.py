"""User agent parsing utility for session management.

This module provides functionality to parse user agent strings and extract
device, browser, and operating system information for session tracking.
"""

from typing import Dict, Optional

try:
    from user_agents import parse
    USER_AGENTS_AVAILABLE = True
except ImportError:
    USER_AGENTS_AVAILABLE = False


def parse_user_agent(user_agent: Optional[str]) -> Dict[str, str]:
    """
    Parse user agent string to extract device, browser, and OS info.
    
    Args:
        user_agent: User agent string from HTTP request
        
    Returns:
        Dictionary with keys: device_type, browser_name, os_name, session_name
        
    Example:
        >>> parse_user_agent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...")
        {
            "device_type": "desktop",
            "browser_name": "Chrome",
            "os_name": "macOS",
            "session_name": "Chrome on macOS"
        }
    """
    if not user_agent:
        return {
            "device_type": "unknown",
            "browser_name": "unknown",
            "os_name": "unknown",
            "session_name": "Unknown Device"
        }
    
    if USER_AGENTS_AVAILABLE:
        return _parse_with_library(user_agent)
    else:
        return _parse_with_regex(user_agent)


def _parse_with_library(user_agent: str) -> Dict[str, str]:
    """Parse user agent using the user-agents library."""
    ua = parse(user_agent)
    
    # Determine device type
    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "unknown"
    
    # Get browser name
    browser_name = ua.browser.family if ua.browser.family else "Unknown"
    
    # Get OS name
    os_name = ua.os.family if ua.os.family else "Unknown"
    
    # Generate session name
    session_name = f"{browser_name} on {os_name}"
    if device_type not in ("desktop", "unknown"):
        session_name = f"{browser_name} on {os_name} ({device_type.title()})"
    
    return {
        "device_type": device_type,
        "browser_name": browser_name,
        "os_name": os_name,
        "session_name": session_name
    }


def _parse_with_regex(user_agent: str) -> Dict[str, str]:
    """
    Parse user agent using simple regex patterns (fallback).
    
    This is a lightweight fallback when the user-agents library is not available.
    It covers the most common user agents but may not be as accurate.
    """
    ua = user_agent.lower()
    
    # Detect device type
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device_type = "mobile"
    elif "tablet" in ua or "ipad" in ua:
        device_type = "tablet"
    else:
        device_type = "desktop"
    
    # Detect browser
    if "edg" in ua:
        browser_name = "Edge"
    elif "chrome" in ua and "edg" not in ua:
        browser_name = "Chrome"
    elif "firefox" in ua:
        browser_name = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser_name = "Safari"
    elif "opera" in ua or "opr" in ua:
        browser_name = "Opera"
    else:
        browser_name = "Unknown"
    
    # Detect OS
    if "windows" in ua:
        if "windows nt 10" in ua:
            os_name = "Windows 10/11"
        elif "windows nt 6.3" in ua:
            os_name = "Windows 8.1"
        elif "windows nt 6.2" in ua:
            os_name = "Windows 8"
        elif "windows nt 6.1" in ua:
            os_name = "Windows 7"
        else:
            os_name = "Windows"
    elif "mac os" in ua or "macos" in ua:
        os_name = "macOS"
    elif "linux" in ua and "android" not in ua:
        os_name = "Linux"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua or "ipod" in ua:
        os_name = "iOS"
    else:
        os_name = "Unknown"
    
    # Generate session name
    session_name = f"{browser_name} on {os_name}"
    if device_type not in ("desktop", "unknown"):
        session_name = f"{browser_name} on {os_name} ({device_type.title()})"
    
    return {
        "device_type": device_type,
        "browser_name": browser_name,
        "os_name": os_name,
        "session_name": session_name
    }
