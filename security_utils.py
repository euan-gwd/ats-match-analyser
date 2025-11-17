"""
Security and GDPR compliance utilities for handling PII in the ATS Match Analyzer.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

# Configure secure logging (don't log PII)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration constants."""

    # Session timeout (30 minutes of inactivity)
    SESSION_TIMEOUT_MINUTES = 30

    # Maximum file sizes (in bytes)
    MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_JD_SIZE = 5 * 1024 * 1024  # 5MB

    # Allowed file types
    ALLOWED_EXTENSIONS = {'.pdf'}

    # Rate limiting
    MAX_REQUESTS_PER_HOUR = 10

    # Data retention
    AUTO_DELETE_AFTER_MINUTES = 30

    # Content security
    MAX_TEXT_LENGTH = 100000  # characters

    # Encryption key (should be set via environment variable in production)
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', secrets.token_hex(32))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components and dangerous characters
    import re
    filename = os.path.basename(filename)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename[:255]  # Limit length


def validate_file_size(file_bytes: bytes, max_size: int) -> bool:
    """
    Validate file size is within limits.

    Args:
        file_bytes: File content
        max_size: Maximum allowed size in bytes

    Returns:
        True if valid, False otherwise
    """
    return len(file_bytes) <= max_size


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension is allowed.

    Args:
        filename: Filename to check

    Returns:
        True if allowed, False otherwise
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in SecurityConfig.ALLOWED_EXTENSIONS


def hash_text(text: str) -> str:
    """
    Create a hash of text for logging/tracking without exposing PII.

    Args:
        text: Text to hash

    Returns:
        SHA256 hash of the text
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def anonymize_for_logging(text: str, max_length: int = 50) -> str:
    """
    Create anonymized version of text for logging.
    Shows only length and hash, no actual content.

    Args:
        text: Original text
        max_length: Maximum length to show

    Returns:
        Anonymized representation
    """
    text_hash = hash_text(text)
    return f"[TEXT_LENGTH:{len(text)}_HASH:{text_hash}]"


def sanitize_url(url: str) -> Optional[str]:
    """
    Validate and sanitize URL to prevent SSRF attacks.

    Args:
        url: URL to validate

    Returns:
        Sanitized URL or None if invalid
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # Only allow https for external URLs
        if parsed.scheme not in ['https', 'http']:
            logger.warning(f"Rejected URL with invalid scheme: {parsed.scheme}")
            return None

        # Block internal/private network addresses
        blocked_hosts = [
            'localhost', '127.0.0.1', '0.0.0.0',
            '169.254.', '10.', '172.16.', '192.168.'
        ]

        if any(parsed.netloc.startswith(blocked) for blocked in blocked_hosts):
            logger.warning(f"Rejected URL with blocked host: {parsed.netloc}")
            return None

        # Prefer HTTPS
        if parsed.scheme == 'http':
            logger.info("HTTP URL detected - recommending HTTPS")

        return url

    except Exception as e:
        logger.error(f"URL validation failed: {str(e)}")
        return None


def scrub_pii_from_logs(text: str) -> str:
    """
    Remove potential PII from text before logging.

    Args:
        text: Text that might contain PII

    Returns:
        Scrubbed text safe for logging
    """
    import re

    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

    # Remove phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b', '[PHONE]', text)

    # Remove names (basic pattern - capitalize words)
    # This is imperfect but helps reduce exposure
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)

    # Remove addresses (basic street patterns)
    text = re.sub(r'\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)', '[ADDRESS]', text)

    # Remove SSN-like patterns
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)

    return text


def secure_session_cleanup(session_state) -> None:
    """
    Securely clean up session data containing PII.

    Args:
        session_state: Streamlit session state object
    """
    pii_keys = [
        'resume_text', 'combined_resume_text', 'linkedin_text',
        'job_text', 'breakdown', 'resume_file', 'linkedin_url'
    ]

    for key in pii_keys:
        if key in session_state:
            # Overwrite with random data before deletion (defense in depth)
            if isinstance(session_state[key], str):
                session_state[key] = secrets.token_hex(16)
            del session_state[key]

    logger.info("Session data securely cleaned up")


def check_session_timeout(session_state) -> bool:
    """
    Check if session has timed out.

    Args:
        session_state: Streamlit session state object

    Returns:
        True if session is still valid, False if timed out
    """
    if 'last_activity' not in session_state:
        session_state.last_activity = datetime.now()
        return True

    time_since_activity = datetime.now() - session_state.last_activity

    if time_since_activity > timedelta(minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES):
        logger.info(f"Session timed out after {time_since_activity}")
        return False

    # Update activity timestamp
    session_state.last_activity = datetime.now()
    return True


def rate_limit_check(session_state) -> tuple[bool, Optional[str]]:
    """
    Check if user has exceeded rate limits.

    Args:
        session_state: Streamlit session state object

    Returns:
        Tuple of (is_allowed, error_message)
    """
    current_time = datetime.now()

    if 'request_history' not in session_state:
        session_state.request_history = []

    # Remove requests older than 1 hour
    session_state.request_history = [
        req_time for req_time in session_state.request_history
        if current_time - req_time < timedelta(hours=1)
    ]

    # Check if limit exceeded
    if len(session_state.request_history) >= SecurityConfig.MAX_REQUESTS_PER_HOUR:
        return False, f"Rate limit exceeded. Maximum {SecurityConfig.MAX_REQUESTS_PER_HOUR} requests per hour."

    # Add current request
    session_state.request_history.append(current_time)
    return True, None


def log_security_event(event_type: str, details: dict) -> None:
    """
    Log security-relevant events without exposing PII.

    Args:
        event_type: Type of security event
        details: Event details (will be scrubbed)
    """
    scrubbed_details = {
        key: anonymize_for_logging(str(value)) if isinstance(value, str) and len(str(value)) > 20 else value
        for key, value in details.items()
    }

    logger.info(f"SECURITY_EVENT: {event_type} - {scrubbed_details}")


def validate_content_safety(text: str) -> tuple[bool, Optional[str]]:
    """
    Basic content validation to prevent injection attacks.

    Args:
        text: Text to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    if not text:
        return True, None

    # Check length
    if len(text) > SecurityConfig.MAX_TEXT_LENGTH:
        return False, f"Content too large. Maximum {SecurityConfig.MAX_TEXT_LENGTH} characters allowed."

    # Check for suspicious patterns (basic XSS/injection prevention)
    suspicious_patterns = [
        '<script', 'javascript:', 'onerror=', 'onload=',
        'eval(', 'exec(', '__import__'
    ]

    text_lower = text.lower()
    for pattern in suspicious_patterns:
        if pattern in text_lower:
            log_security_event('SUSPICIOUS_CONTENT_DETECTED', {
                'pattern': pattern,
                'text_hash': hash_text(text)
            })
            return False, "Suspicious content detected. Please remove any scripts or code."

    return True, None
