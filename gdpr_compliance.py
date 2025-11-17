"""
GDPR compliance utilities for the ATS Match Analyzer.
Implements data protection, user rights, and privacy requirements.
"""

import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class GDPRCompliance:
    """Handle GDPR compliance requirements."""

    @staticmethod
    def get_privacy_notice() -> str:
        """
        Return GDPR-compliant privacy notice.

        Returns:
            Privacy notice text
        """
        return """
### 🔒 Privacy Notice & Data Protection

**Last Updated:** November 2025

#### What Data We Process
This application processes the following personal data:
- Resume/CV content (including name, contact information, work history, education)
- LinkedIn profile information (if provided)
- Job description text
- Analysis timestamps and session data

#### Legal Basis for Processing
We process your data based on your **explicit consent** (GDPR Art. 6(1)(a)).

#### How We Use Your Data
Your data is used solely to:
- Analyze your resume against job descriptions
- Generate personalized improvement recommendations
- Provide ATS scoring and optimization suggestions

#### Data Storage & Retention
- **No server-side storage**: All processing happens in your browser session
- **Automatic deletion**: All data is deleted when you close your browser or after 30 minutes of inactivity
- **No cloud storage**: We do not store your resume, LinkedIn data, or any personal information on our servers
- **No third-party sharing**: Your data is never shared with third parties

#### Your Rights Under GDPR
You have the right to:
- ✅ **Access** your data (already visible in your session)
- ✅ **Rectification** (you control the input data)
- ✅ **Erasure** (clear your session or close the browser)
- ✅ **Data portability** (download your analysis results)
- ✅ **Withdraw consent** (stop using the service at any time)
- ✅ **Object to processing** (don't submit data if you object)

#### Data Security
We implement:
- TLS/HTTPS encryption for data in transit
- Client-side processing where possible
- No persistent storage of personal data
- Session timeouts and automatic cleanup
- Rate limiting to prevent abuse

#### International Data Transfers
All processing occurs within your browser. If you access from outside the EU,
your data is processed locally on your device.

#### Contact & Data Protection Officer
For privacy concerns or to exercise your rights, contact: [YOUR-EMAIL]

#### Cookies
This application uses minimal session cookies required for functionality.
No tracking or analytics cookies are used without your consent.

By using this service, you acknowledge that you have read and understood this privacy notice.
"""

    @staticmethod
    def get_consent_text() -> str:
        """
        Return consent text for GDPR compliance.

        Returns:
            Consent text
        """
        return """
**I consent to the processing of my personal data** (including resume content, LinkedIn profile,
and job description information) for the purpose of ATS analysis and resume optimization as
described in the Privacy Notice.

I understand that:
- My data will be processed in accordance with GDPR
- I can withdraw consent at any time by closing my browser session
- My data will be automatically deleted after 30 minutes of inactivity
- No data is stored permanently on servers
"""

    @staticmethod
    def log_consent(session_id: str, consent_given: bool) -> None:
        """
        Log user consent (anonymized).

        Args:
            session_id: Anonymized session identifier
            consent_given: Whether consent was given
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_hash': session_id[:8],  # Only first 8 chars for privacy
            'consent_given': consent_given,
            'action': 'CONSENT_RECORDED'
        }
        logger.info(f"GDPR_CONSENT: {json.dumps(log_entry)}")

    @staticmethod
    def log_data_deletion(session_id: str, reason: str) -> None:
        """
        Log data deletion for audit trail.

        Args:
            session_id: Anonymized session identifier
            reason: Reason for deletion (timeout, manual, etc.)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_hash': session_id[:8],
            'reason': reason,
            'action': 'DATA_DELETED'
        }
        logger.info(f"GDPR_DELETION: {json.dumps(log_entry)}")

    @staticmethod
    def get_data_processing_agreement() -> dict:
        """
        Return data processing agreement details.

        Returns:
            Dictionary with DPA details
        """
        return {
            'controller': 'ATS Match Analyzer',
            'purpose': 'Resume analysis and optimization',
            'categories_of_data': [
                'Name and contact information',
                'Professional experience and education',
                'Skills and qualifications',
                'LinkedIn profile data (optional)'
            ],
            'retention_period': '30 minutes (session-based)',
            'recipients': 'None - no third-party sharing',
            'security_measures': [
                'TLS/HTTPS encryption',
                'Session-based processing',
                'No persistent storage',
                'Automatic data deletion',
                'Rate limiting',
                'Input validation'
            ],
            'user_rights': [
                'Right to access',
                'Right to rectification',
                'Right to erasure',
                'Right to data portability',
                'Right to withdraw consent',
                'Right to object'
            ]
        }


class DataMinimization:
    """Implement GDPR data minimization principles."""

    @staticmethod
    def should_process_field(field_name: str, purpose: str) -> bool:
        """
        Determine if a field should be processed based on necessity.

        Args:
            field_name: Name of the data field
            purpose: Purpose of processing

        Returns:
            True if field is necessary for the purpose
        """
        # Map purposes to necessary fields
        necessary_fields = {
            'ats_scoring': ['resume_text', 'job_text', 'skills', 'experience'],
            'optimization': ['resume_text', 'job_text', 'linkedin_text'],
            'analysis': ['resume_text', 'job_text']
        }

        return field_name in necessary_fields.get(purpose, [])

    @staticmethod
    def minimize_retention(data: dict) -> dict:
        """
        Remove unnecessary fields from data to minimize retention.

        Args:
            data: Data dictionary

        Returns:
            Minimized data dictionary
        """
        # Keep only essential fields for analysis results
        essential_fields = {
            'overall_score', 'keyword_similarity', 'skills_coverage',
            'seniority_alignment', 'ats_friendliness', 'recommendations'
        }

        return {k: v for k, v in data.items() if k in essential_fields}


class AuditLog:
    """Maintain GDPR-compliant audit log."""

    @staticmethod
    def log_processing_activity(
        activity: str,
        session_id: str,
        data_categories: list[str],
        legal_basis: str = 'consent'
    ) -> None:
        """
        Log data processing activity for GDPR compliance.

        Args:
            activity: Description of processing activity
            session_id: Anonymized session ID
            data_categories: Categories of data processed
            legal_basis: Legal basis for processing
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'activity': activity,
            'session_hash': session_id[:8],
            'data_categories': data_categories,
            'legal_basis': legal_basis,
            'retention': '30 minutes'
        }
        logger.info(f"GDPR_AUDIT: {json.dumps(log_entry)}")


def get_data_export(session_data: dict) -> dict:
    """
    Generate GDPR-compliant data export for user.

    Args:
        session_data: User's session data

    Returns:
        Exportable data dictionary
    """
    return {
        'export_date': datetime.now().isoformat(),
        'data_subject_rights': 'This export fulfills your right to data portability under GDPR Art. 20',
        'analysis_results': {
            'overall_score': session_data.get('breakdown', {}).get('overall', 0),
            'subscores': {
                'keyword_similarity': session_data.get('breakdown', {}).get('keyword_similarity', 0),
                'skills_coverage': session_data.get('breakdown', {}).get('skills_coverage', 0),
                'seniority_alignment': session_data.get('breakdown', {}).get('seniority_alignment', 0),
                'ats_friendliness': session_data.get('breakdown', {}).get('ats_friendliness', 0),
            },
            'recommendations': 'Available in the UI',
            'timestamp': datetime.now().isoformat()
        },
        'note': 'Your resume and personal data are not included in this export for security reasons. They are session-only and will be automatically deleted.'
    }
