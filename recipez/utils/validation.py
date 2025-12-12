"""
Security validation utilities for user input.
Prevents XSS, path traversal, and other injection attacks.
"""

import re
from urllib.parse import urlparse


def validate_image_url(url) -> bool:
    """
    Validate image URL is safe and well-formed.

    Prevents:
    - XSS via javascript:, data:, vbscript: schemes
    - Path traversal via ../ sequences
    - File extension attacks (.js, .php, .exe)
    - Event handler injection (onerror, onload)

    Args:
        url: User-provided image URL string

    Returns:
        bool: True if URL is safe, False otherwise

    Security:
        - Only allows /static/img/ and /static/uploads/ paths
        - Validates file extensions (png, jpg, jpeg only)
        - Rejects dangerous URL components
        - Limits path depth to prevent traversal
    """
    # Type validation
    if not url or not isinstance(url, str):
        return False

    # Case-insensitive danger checks
    url_lower = url.lower()

    # Block dangerous URL schemes
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
    if any(scheme in url_lower for scheme in dangerous_schemes):
        return False

    # Block event handler injections
    dangerous_handlers = ['onerror', 'onload', 'onclick', 'onmouseover']
    if any(handler in url_lower for handler in dangerous_handlers):
        return False

    # Only allow relative paths starting with /static/
    if not url.startswith('/static/'):
        return False

    # Prevent path traversal
    if '..' in url:
        return False

    # Limit path depth (max 4 segments: /static/uploads/filename.png or /static/img/filename.png)
    if url.count('/') > 4:
        return False

    # Validate path pattern and file extension
    # Pattern 1: /static/img/[alphanumeric-_].(png|jpg|jpeg)
    # Pattern 2: /static/uploads/[alphanumeric-_].(png|jpg|jpeg)
    img_pattern = r'^/static/img/[a-zA-Z0-9_-]+\.(png|jpg|jpeg)$'
    uploads_pattern = r'^/static/uploads/[a-zA-Z0-9_-]+\.(png|jpg|jpeg)$'

    if re.match(img_pattern, url) or re.match(uploads_pattern, url):
        return True

    return False
