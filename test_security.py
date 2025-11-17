"""
Security and GDPR compliance tests.
"""

import pytest
from datetime import datetime, timedelta
from security_utils import (
    sanitize_filename,
    sanitize_url,
    validate_file_size,
    validate_file_extension,
    validate_content_safety,
    hash_text,
    scrub_pii_from_logs,
    SecurityConfig
)
from gdpr_compliance import GDPRCompliance, DataMinimization


class TestFileSecurity:
    """Test file upload security."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("resume.pdf") == "resume.pdf"
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("resume<script>.pdf") == "resume_script_.pdf"
        assert sanitize_filename("path/to/resume.pdf") == "resume.pdf"

    def test_validate_file_extension(self):
        """Test file extension validation."""
        assert validate_file_extension("resume.pdf") == True
        assert validate_file_extension("resume.exe") == False
        assert validate_file_extension("resume.PDF") == True
        assert validate_file_extension("resume.docx") == False

    def test_validate_file_size(self):
        """Test file size validation."""
        small_file = b"test content"
        assert validate_file_size(small_file, 1024) == True

        large_file = b"x" * (11 * 1024 * 1024)  # 11MB
        assert validate_file_size(large_file, SecurityConfig.MAX_RESUME_SIZE) == False


class TestURLSecurity:
    """Test URL validation and sanitization."""

    def test_sanitize_url_valid(self):
        """Test valid URL sanitization."""
        assert sanitize_url("https://example.com") == "https://example.com"
        assert sanitize_url("https://linkedin.com/in/user") == "https://linkedin.com/in/user"

    def test_sanitize_url_blocked(self):
        """Test blocked URL patterns."""
        assert sanitize_url("http://localhost/") is None
        assert sanitize_url("http://127.0.0.1/") is None
        assert sanitize_url("http://192.168.1.1/") is None
        assert sanitize_url("javascript:alert(1)") is None
        assert sanitize_url("file:///etc/passwd") is None

    def test_sanitize_url_ssrf_prevention(self):
        """Test SSRF attack prevention."""
        assert sanitize_url("http://169.254.169.254/latest/meta-data/") is None
        assert sanitize_url("http://10.0.0.1/") is None
        assert sanitize_url("http://172.16.0.1/") is None


class TestContentSafety:
    """Test content validation."""

    def test_validate_safe_content(self):
        """Test safe content passes validation."""
        safe_text = "This is a normal resume with work experience at Company ABC."
        is_safe, error = validate_content_safety(safe_text)
        assert is_safe == True
        assert error is None

    def test_validate_script_injection(self):
        """Test script injection detection."""
        malicious = "My resume <script>alert('xss')</script>"
        is_safe, error = validate_content_safety(malicious)
        assert is_safe == False
        assert "suspicious" in error.lower()

    def test_validate_javascript_injection(self):
        """Test JavaScript injection detection."""
        malicious = "Check my portfolio at javascript:alert(1)"
        is_safe, error = validate_content_safety(malicious)
        assert is_safe == False

    def test_validate_length_limit(self):
        """Test content length validation."""
        too_long = "x" * (SecurityConfig.MAX_TEXT_LENGTH + 1)
        is_safe, error = validate_content_safety(too_long)
        assert is_safe == False
        assert "too large" in error.lower()


class TestPIIProtection:
    """Test PII scrubbing and protection."""

    def test_hash_text(self):
        """Test text hashing for logging."""
        text = "John Doe, john@example.com"
        hash1 = hash_text(text)
        hash2 = hash_text(text)

        assert len(hash1) == 16  # First 16 chars of SHA256
        assert hash1 == hash2  # Same text produces same hash
        assert hash1 != text  # Hash is different from original

    def test_scrub_email(self):
        """Test email scrubbing from logs."""
        text = "Contact me at john.doe@example.com for opportunities"
        scrubbed = scrub_pii_from_logs(text)
        assert "john.doe@example.com" not in scrubbed
        assert "[EMAIL]" in scrubbed

    def test_scrub_phone(self):
        """Test phone number scrubbing."""
        text = "Call me at 555-123-4567 or +1-555-123-4567"
        scrubbed = scrub_pii_from_logs(text)
        assert "555-123-4567" not in scrubbed
        assert "[PHONE]" in scrubbed

    def test_scrub_name(self):
        """Test name pattern scrubbing."""
        text = "My name is John Smith and I work at Company"
        scrubbed = scrub_pii_from_logs(text)
        assert "[NAME]" in scrubbed

    def test_scrub_multiple_pii(self):
        """Test scrubbing multiple PII types."""
        text = "John Doe, john@example.com, 555-123-4567, 123 Main Street"
        scrubbed = scrub_pii_from_logs(text)
        assert "[NAME]" in scrubbed
        assert "[EMAIL]" in scrubbed
        assert "[PHONE]" in scrubbed
        assert "[ADDRESS]" in scrubbed


class TestGDPRCompliance:
    """Test GDPR compliance features."""

    def test_privacy_notice_exists(self):
        """Test privacy notice is available."""
        notice = GDPRCompliance.get_privacy_notice()
        assert len(notice) > 100
        assert "GDPR" in notice
        assert "consent" in notice.lower()
        assert "data protection" in notice.lower()

    def test_consent_text_exists(self):
        """Test consent text is available."""
        consent = GDPRCompliance.get_consent_text()
        assert len(consent) > 50
        assert "consent" in consent.lower()
        assert "withdraw" in consent.lower()

    def test_dpa_completeness(self):
        """Test Data Processing Agreement is complete."""
        dpa = GDPRCompliance.get_data_processing_agreement()

        assert "purpose" in dpa
        assert "categories_of_data" in dpa
        assert "retention_period" in dpa
        assert "security_measures" in dpa
        assert "user_rights" in dpa

        # Check user rights are complete
        rights = dpa["user_rights"]
        assert "Right to access" in rights
        assert "Right to erasure" in rights
        assert "Right to data portability" in rights


class TestDataMinimization:
    """Test data minimization principles."""

    def test_should_process_field(self):
        """Test field processing necessity."""
        # Necessary fields
        assert DataMinimization.should_process_field("resume_text", "ats_scoring") == True
        assert DataMinimization.should_process_field("job_text", "ats_scoring") == True

        # Unnecessary fields
        assert DataMinimization.should_process_field("home_address", "ats_scoring") == False
        assert DataMinimization.should_process_field("photo", "ats_scoring") == False

    def test_minimize_retention(self):
        """Test data retention minimization."""
        full_data = {
            "overall_score": 85,
            "resume_text": "Full resume content...",
            "job_text": "Full job description...",
            "recommendations": ["Add Python", "Add leadership"],
            "user_email": "user@example.com",
            "timestamp": "2025-01-01"
        }

        minimized = DataMinimization.minimize_retention(full_data)

        # Should keep analysis results
        assert "overall_score" in minimized
        assert "recommendations" in minimized

        # Should remove raw PII
        assert "resume_text" not in minimized
        assert "job_text" not in minimized
        assert "user_email" not in minimized


class TestSessionManagement:
    """Test session security features."""

    def test_session_cleanup(self):
        """Test secure session cleanup."""
        from security_utils import secure_session_cleanup

        class MockSession(dict):
            """Mock session state."""
            pass

        session = MockSession()
        session['resume_text'] = "Sensitive resume content"
        session['job_text'] = "Job description"
        session['breakdown'] = {"score": 85}

        secure_session_cleanup(session)

        # Check all PII is removed
        assert 'resume_text' not in session
        assert 'job_text' not in session
        assert 'breakdown' not in session


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_enforcement(self):
        """Test rate limit is enforced."""
        from security_utils import rate_limit_check

        class MockSession(dict):
            """Mock session state."""
            pass

        session = MockSession()

        # Should allow first requests
        for i in range(SecurityConfig.MAX_REQUESTS_PER_HOUR):
            is_allowed, error = rate_limit_check(session)
            assert is_allowed == True

        # Should block after limit
        is_allowed, error = rate_limit_check(session)
        assert is_allowed == False
        assert "rate limit" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
