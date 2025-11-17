import io
import secrets
from datetime import date
from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup
from pypdf import PdfReader

from ats_scoring import score_resume_against_job
from resume_optimizer import build_optimized_resume, build_optimized_resume_docx
from security_utils import (
    SecurityConfig,
    sanitize_filename,
    sanitize_url,
    validate_content_safety,
    validate_file_extension,
    validate_file_size,
    check_session_timeout,
    rate_limit_check,
    secure_session_cleanup,
    log_security_event,
    hash_text
)
from gdpr_compliance import (
    GDPRCompliance,
    AuditLog,
    get_data_export
)


def _extract_job_phrases(job_text: str) -> dict:
    """Extract specific phrases and requirements from job description."""
    import re

    jd_lower = job_text.lower()

    # Extract role title
    role_patterns = [
        r'(?:position|role|title):\s*([^\n]{10,60})',
        r'^([A-Z][^\n]{10,60}(?:engineer|developer|manager|analyst|scientist|designer))',
    ]
    role_title = None
    for pattern in role_patterns:
        match = re.search(pattern, job_text, re.MULTILINE | re.IGNORECASE)
        if match:
            role_title = match.group(1).strip()
            break

    # Extract years of experience requirements
    years_match = re.search(r'(\d+)\+?\s+years?\s+(?:of\s+)?(?:experience|exp)', jd_lower)
    required_years = years_match.group(1) if years_match else None

    # Extract key responsibility phrases (look for bullet points or "you will")
    responsibilities = []
    resp_patterns = [
        r'(?:•|\*|-|\d+\.)\s*([^\n]{20,120})',
        r'you will\s+([^\n]{20,100})',
        r'responsible for\s+([^\n]{20,100})',
    ]
    for pattern in resp_patterns:
        matches = re.findall(pattern, jd_lower)
        responsibilities.extend([m.strip() for m in matches[:5]])

    # Extract required vs preferred qualifications
    required_section = re.search(r'required(?:\s+qualifications)?:?(.*?)(?:preferred|nice to have|$)', jd_lower, re.DOTALL | re.IGNORECASE)
    preferred_section = re.search(r'(?:preferred|nice to have|bonus)(?:\s+qualifications)?:?(.*?)(?:$|\n\n)', jd_lower, re.DOTALL | re.IGNORECASE)

    return {
        'role_title': role_title,
        'required_years': required_years,
        'responsibilities': responsibilities[:5],
        'required_text': required_section.group(1)[:500] if required_section else "",
        'preferred_text': preferred_section.group(1)[:300] if preferred_section else "",
    }


def _analyze_resume_gaps(job_text: str, resume_text: str, missing_keywords: list, linkedin_text: str = "") -> dict:
    """Generate specific, actionable changes based on actual content analysis."""
    import re

    actions = []
    jd_lower = job_text.lower()
    cv_lower = resume_text.lower()
    linkedin_lower = linkedin_text.lower() if linkedin_text else ""

    # Check for specific phrases in JD that should be mirrored
    key_phrases = []

    # Extract important 2-3 word phrases from JD
    jd_keywords = re.findall(r'\b(?:[a-z]+ ){1,2}[a-z]+\b', jd_lower)
    phrase_counts = {}
    for phrase in jd_keywords:
        phrase = phrase.strip()
        if len(phrase) > 8 and phrase not in phrase_counts:
            phrase_counts[phrase] = jd_lower.count(phrase)

    # Get most frequent phrases not in resume
    important_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
    for phrase, count in important_phrases[:10]:
        if count >= 2 and phrase not in cv_lower:
            key_phrases.append(phrase)

    # Check if resume has a summary/objective
    has_summary = bool(re.search(r'(?:summary|objective|profile|about):', cv_lower))

    # Check for quantified achievements
    has_metrics = bool(re.search(r'\d+%|\$\d+|\d+\+?\s+(?:users|people|employees|projects)', cv_lower))

    # LinkedIn-specific analysis: find content in LinkedIn but missing from CV
    linkedin_additions = []
    linkedin_has_better_metrics = False

    if linkedin_lower and len(linkedin_lower) > 100:
        # Find skills/keywords in LinkedIn that match JD but are missing from CV
        for keyword in missing_keywords[:15]:
            if keyword in linkedin_lower and keyword not in cv_lower:
                # Try to find context in LinkedIn
                context_match = re.search(rf'([^.!?\n]{0,60}{re.escape(keyword)}[^.!?\n]{0,60})[.!?\n]', linkedin_lower)
                if context_match:
                    context = context_match.group(1).strip()[:100]
                    linkedin_additions.append({
                        'keyword': keyword,
                        'context': context
                    })

        # Check if LinkedIn has metrics that CV lacks
        if not has_metrics:
            linkedin_metrics = re.findall(r'\d+%|\$[\d,]+|\d+\+?\s+(?:users|people|employees|projects|customers)', linkedin_lower)
            if len(linkedin_metrics) > 2:
                linkedin_has_better_metrics = True

    return {
        'key_phrases': key_phrases[:5],
        'has_summary': has_summary,
        'has_metrics': has_metrics,
        'missing_critical': [k for k in missing_keywords[:8] if k in jd_lower and k not in cv_lower],
        'linkedin_additions': linkedin_additions[:8],
        'linkedin_has_metrics': linkedin_has_better_metrics
    }


def generate_actionable_steps(breakdown, job_text: str, resume_text: str, linkedin_text: str = "") -> list[dict]:
    """Generate specific, actionable changes based on actual job description and resume analysis."""
    import re
    steps = []

    # Extract actual content from JD and CV
    jd_analysis = _extract_job_phrases(job_text)
    gap_analysis = _analyze_resume_gaps(job_text, resume_text, breakdown.missing_keywords, linkedin_text)

    # CRITICAL: Missing keywords that are in JD requirements
    if breakdown.skills_coverage < 70 and gap_analysis['missing_critical']:
        specific_actions = []

        for keyword in gap_analysis['missing_critical'][:5]:
            # Find full context sentence in JD
            sentences = re.split(r'[.!?]+', job_text)
            context_sentence = ""
            for sent in sentences:
                if keyword in sent.lower():
                    context_sentence = sent.strip()[:100]
                    break

            if context_sentence:
                specific_actions.append(
                    f'• **"{keyword}"** - JD says: "{context_sentence}..." '
                    f'→ Add to Skills section + mention in a relevant job bullet'
                )
            else:
                specific_actions.append(f'• **"{keyword}"** → Add to Skills section + describe where you used it')

        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Missing Required Keywords",
            "action": f"Add these {len(gap_analysis['missing_critical'][:5])} critical keywords",
            "details": specific_actions,
            "impact": f"Score: {breakdown.skills_coverage:.0f}% → {min(90, breakdown.skills_coverage + 25):.0f}%"
        })

    # CRITICAL: LinkedIn content that should be in CV
    if gap_analysis['linkedin_additions']:
        linkedin_actions = []

        for idx, item in enumerate(gap_analysis['linkedin_additions'][:5], 1):
            keyword = item['keyword']
            context = item['context']
            linkedin_actions.append(
                f'{idx}. **"{keyword}"** - Your LinkedIn says: "{context}" '
                f'→ Copy this to your CV Skills/Experience section'
            )

        if len(gap_analysis['linkedin_additions']) > 5:
            linkedin_actions.append(f"...plus {len(gap_analysis['linkedin_additions']) - 5} more on your LinkedIn")

        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Copy from Your LinkedIn",
            "action": "Copy these existing descriptions from your LinkedIn profile",
            "details": linkedin_actions,
            "impact": f"Instant add of {len(gap_analysis['linkedin_additions'])} missing keywords"
        })

    # CRITICAL: Mirror specific language from JD
    if breakdown.keyword_similarity < 70 and gap_analysis['key_phrases']:
        phrase_actions = []

        if jd_analysis['role_title']:
            phrase_actions.append(
                f'• **Line 1 of CV**: Change to "{jd_analysis["role_title"]} with [X] years in [top 3 skills]"'
            )

        for phrase in gap_analysis['key_phrases'][:3]:
            # Find where this phrase appears in JD
            sentences = re.split(r'[.!?]+', job_text)
            phrase_context = ""
            for sent in sentences:
                if phrase in sent.lower():
                    phrase_context = sent.strip()[:100]
                    break

            if phrase_context:
                phrase_actions.append(
                    f'• Use **"{phrase}"**: JD says "{phrase_context}..." '
                    f'→ Add this phrase in 2-3 Experience bullets'
                )
            else:
                phrase_actions.append(f'• Use phrase **"{phrase}"** → Add in Experience bullets')

        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Use JD's Exact Language",
            "action": "Replace your words with these exact JD phrases",
            "details": phrase_actions,
            "impact": f"Score: {breakdown.keyword_similarity:.0f}% → {min(90, breakdown.keyword_similarity + 20):.0f}%"
        })

    # HIGH: Add/improve professional summary
    if not gap_analysis['has_summary'] or breakdown.keyword_similarity < 75:
        summary_bullets = []

        if not gap_analysis['has_summary']:
            summary_bullets.append('❌ **MISSING: Professional Summary at top of CV**')

        # Build the template
        template_parts = []
        if jd_analysis['role_title']:
            template_parts.append(f"{jd_analysis['role_title']}")
        else:
            template_parts.append("[Role from JD]")

        if jd_analysis['required_years']:
            template_parts.append(f"with {jd_analysis['required_years']}+ years")
        else:
            template_parts.append("with [X] years")

        if breakdown.missing_keywords[:3]:
            template_parts.append(f"in {', '.join(breakdown.missing_keywords[:3])}")

        template = " ".join(template_parts) + ". [One achievement]. [One goal from JD]."

        summary_bullets.append(f'**Copy this template**: "{template}"')

        if jd_analysis['required_years']:
            summary_bullets.append(f'⚠️ Must state "{jd_analysis["required_years"]}+ years" - JD requires it')

        steps.append({
            "priority": "🟡 HIGH",
            "category": "Professional Summary",
            "action": "Add summary as first section (right after name/contact)",
            "details": summary_bullets,
            "impact": "Summary read first by ATS - 15-20% of total score"
        })

    # HIGH: ATS formatting issues
    if breakdown.ats_friendliness < 80 and breakdown.ats_reasons:
        format_actions = []
        for reason in breakdown.ats_reasons:
            if "short" in reason.lower() or "long" in reason.lower():
                format_actions.append(f'• {reason} → Aim for 2 pages, 3-4 bullets per job')
            elif "column" in reason.lower() or "layout" in reason.lower():
                format_actions.append(f'• {reason} → Use single-column, save as PDF from Word/Docs')
            elif "header" in reason.lower() or "section" in reason.lower():
                format_actions.append(f'• {reason} → Add bold headings: Summary, Experience, Education, Skills')
            else:
                format_actions.append(f'• {reason}')

        steps.append({
            "priority": "🟡 HIGH",
            "category": "ATS Format Issues",
            "action": "Fix formatting so ATS can parse your CV",
            "details": format_actions,
            "impact": f"Score: {breakdown.ats_friendliness:.0f}% → 95%"
        })

    # HIGH: Quantify achievements
    if not gap_analysis['has_metrics']:
        metrics_actions = []

        if gap_analysis.get('linkedin_has_metrics'):
            metrics_actions.append('🔗 Your LinkedIn has numbers - copy those bullets to CV!')

        # Find a verb from their resume
        cv_verbs = re.findall(r'\b(Led|Managed|Developed|Improved|Increased|Reduced|Created|Built|Designed|Implemented)\b', resume_text, re.IGNORECASE)
        verb = cv_verbs[0] if cv_verbs else "Led"

        metrics_actions.extend([
            f'• ❌ "{verb} projects" → ✅ "{verb} **5-person team** on **3 projects** over **18 months**"',
            f'• ❌ "Improved performance" → ✅ "Improved performance by **60%** for **10K+ users**"',
            f'• ❌ "Reduced costs" → ✅ "Reduced costs by **$50K annually**"',
            '→ Add numbers to 3+ bullets: team size, %, $, time, users impacted'
        ])

        steps.append({
            "priority": "🟡 HIGH",
            "category": "Add Numbers",
            "action": "Quantify 3+ achievements with %, $, or team size",
            "details": metrics_actions,
            "impact": "Quantified bullets score 3X higher - worth 20-25%"
        })

    # MEDIUM: Seniority alignment
    if breakdown.seniority_alignment < 80:
        seniority_actions = [f'⚠️ {breakdown.seniority_explanation}']

        if jd_analysis['required_years']:
            seniority_actions.append(
                f'• Add to Line 1: "{jd_analysis["required_years"]}+ years of experience in [field]"'
            )

        jd_lower = job_text.lower()
        if any(word in jd_lower for word in ['lead', 'senior', 'principal', 'architect']):
            seniority_actions.append(
                '• Replace weak verbs: "Helped"→"Architected", "Assisted"→"Led", "Supported"→"Drove"'
            )
            seniority_actions.append(
                '• Add leadership: "Mentored 4 developers", "Led team of 8", "Managed $500K budget"'
            )

        steps.append({
            "priority": "🟡 MEDIUM",
            "category": "Seniority Signals",
            "action": "Match the seniority level this job requires",
            "details": seniority_actions,
            "impact": f"Score: {breakdown.seniority_alignment:.0f}% → {min(95, breakdown.seniority_alignment + 15):.0f}%"
        })

    # OPTIMIZATION: Already strong
    if breakdown.skills_coverage >= 70 and breakdown.keyword_similarity >= 70:
        optimize_actions = [
            f'✅ Strong resume ({breakdown.overall:.0f}/100)! Polish:',
            f'• Repeat these keywords 2-3x: {", ".join(breakdown.matched_keywords[:5])}',
            '• Reorder: Put most relevant job first (doesn\'t have to be most recent)',
        ]

        if breakdown.missing_keywords[5:10]:
            optimize_actions.append(f'• Add if true: {", ".join(breakdown.missing_keywords[5:10])}')

        steps.append({
            "priority": "🟢 OPTIMIZE",
            "category": "Final Polish",
            "action": "Fine-tune your strong resume",
            "details": optimize_actions,
            "impact": f"{breakdown.overall:.0f} → 90-95 score"
        })

    return steps


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            pages_text.append(text)
        return "\n".join(pages_text)
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}") from e


def fetch_text_from_url(url: str) -> str:
    """Fetch text content from a job posting URL."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL: {e}") from e

    soup = BeautifulSoup(resp.text, "html.parser")

    # Prefer main content / article if present
    main = soup.find("main") or soup.find("article")
    text_container = main if main else soup.body

    if not text_container:
        return soup.get_text(separator="\n")

    # Remove obvious non-content elements
    for tag in text_container.find_all(["script", "style", "noscript", "nav", "footer", "header", "svg"]):
        tag.decompose()

    text = text_container.get_text(separator="\n")
    return text


def get_job_description_text(
    mode: str,
    pasted_text: Optional[str],
    jd_pdf_file,
    jd_url: Optional[str],
) -> str:
    if mode == "Paste text":
        return (pasted_text or "").strip()
    if mode == "Upload PDF":
        if not jd_pdf_file:
            return ""
        return extract_text_from_pdf(jd_pdf_file.read())
    if mode == "Job URL":
        if not jd_url:
            return ""
        return fetch_text_from_url(jd_url)
    return ""


def get_linkedin_profile_text(linkedin_url: Optional[str]) -> str:
    """
    Best-effort extraction of public LinkedIn profile text.
    Note: This will only work for publicly viewable profiles without login walls.
    """
    if not linkedin_url:
        return ""
    try:
        text = fetch_text_from_url(linkedin_url)
    except RuntimeError:
        return ""
    return text


def main() -> None:
    st.set_page_config(
        page_title="ATS Match Analyzer",
        page_icon="📄",
        layout="wide",
    )

    # Initialize session ID for GDPR audit logging
    if 'session_id' not in st.session_state:
        st.session_state.session_id = secrets.token_hex(16)

    # Check session timeout
    if not check_session_timeout(st.session_state):
        st.warning("⏱️ Your session has timed out for security. Please refresh to start a new session.")
        secure_session_cleanup(st.session_state)
        log_security_event('SESSION_TIMEOUT', {'session_id': st.session_state.session_id})
        st.stop()

    # GDPR Consent Check
    if 'gdpr_consent' not in st.session_state:
        st.session_state.gdpr_consent = False

    if not st.session_state.gdpr_consent:
        st.title("📄 ATS Match Analyzer")
        st.markdown("### Welcome! Privacy & Data Protection First")

        with st.expander("🔒 Privacy Notice (Click to Read)", expanded=True):
            st.markdown(GDPRCompliance.get_privacy_notice())

        st.markdown("---")
        st.markdown(GDPRCompliance.get_consent_text())

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ I Consent & Accept", type="primary", use_container_width=True):
                st.session_state.gdpr_consent = True
                GDPRCompliance.log_consent(st.session_state.session_id, True)
                AuditLog.log_processing_activity(
                    'USER_CONSENT_GIVEN',
                    st.session_state.session_id,
                    ['resume', 'linkedin', 'job_description']
                )
                st.rerun()

        with col2:
            if st.button("❌ I Do Not Consent", use_container_width=True):
                GDPRCompliance.log_consent(st.session_state.session_id, False)
                st.info("You must consent to data processing to use this service. No data has been collected.")
                st.stop()

        st.stop()

    st.title("📄 ATS Match Analyzer")
    st.markdown(
        "Evaluate how your resume is likely to perform in a modern ATS against a specific job posting."
    )

    # Add privacy controls
    with st.sidebar:
        st.markdown("---")
        with st.expander("🔒 Privacy Controls"):
            if st.button("🗑️ Delete My Data & End Session", use_container_width=True):
                secure_session_cleanup(st.session_state)
                GDPRCompliance.log_data_deletion(st.session_state.session_id, 'user_requested')
                st.success("All your data has been securely deleted.")
                st.info("Please refresh the page to start a new session.")
                st.stop()

            if st.button("📥 Export My Analysis Data", use_container_width=True):
                if st.session_state.get('analysis_complete'):
                    export_data = get_data_export(st.session_state)
                    st.download_button(
                        "Download JSON",
                        data=str(export_data),
                        file_name=f"ats_analysis_{date.today().isoformat()}.json",
                        mime="application/json"
                    )
                else:
                    st.info("Complete an analysis first to export data.")

            st.caption("🔒 Your data is session-only and auto-deletes after 30 min of inactivity")

    with st.sidebar:
        st.header("Job description")
        jd_mode = st.radio(
            "How do you want to provide the job description?",
            ("Paste text", "Job URL", "Upload PDF"),
        )

        jd_text_input = None
        jd_pdf_file = None
        jd_url_input = None

        if jd_mode == "Paste text":
            jd_text_input = st.text_area(
                "Paste the full job description",
                height=260,
                placeholder="Paste the responsibilities, requirements, and qualifications here...",
            )
        elif jd_mode == "Upload PDF":
            jd_pdf_file = st.file_uploader(
                "Upload job description PDF",
                type=["pdf"],
                help="Export the job description as PDF and upload it here.",
            )
        else:  # Job URL
            jd_url_input = st.text_input(
                "Job posting URL",
                placeholder="https://careers.example.com/jobs/1234",
            )

        st.header("Job posting date")
        unknown_date = st.checkbox(
            "I don't know the posting date",
            help="If checked, the app will ignore recency when explaining your score.",
        )
        posting_date: Optional[date]
        if unknown_date:
            posting_date = None
        else:
            posting_date = st.date_input(
                "When was the job posted? (approximate is fine)",
                help="Used to reason about posting recency and competition. Pick your best guess.",
            )

        st.header("Your resume")
        resume_file = st.file_uploader(
            "Upload your resume (PDF)",
            type=["pdf"],
            help="Use a clean, single-column PDF exported from Word/Google Docs for best ATS parsing.",
        )

        st.header("LinkedIn profile (optional)")
        st.caption(
            "You can provide a public LinkedIn profile URL. "
            "Content will be merged with your resume text for scoring and optimization, "
            "but **no new facts will be invented**."
        )
        linkedin_url_sidebar = st.text_input(
            "Public LinkedIn profile URL (optional)",
            placeholder="https://www.linkedin.com/in/your-profile",
        )

        analyze_button = st.button("Analyze match", type="primary")

    # Main content area
    if analyze_button:
        # Rate limiting check
        is_allowed, error_msg = rate_limit_check(st.session_state)
        if not is_allowed:
            st.error(f"🚫 {error_msg}")
            log_security_event('RATE_LIMIT_EXCEEDED', {'session_id': st.session_state.session_id})
            return

        # Clear previous generation state
        st.session_state.docx_generated = False
        st.session_state.text_generated = False

        with st.spinner("Parsing documents and emulating ATS scoring..."):
            # Validate and get job description
            job_text = ""

            if jd_mode == "Paste text":
                job_text = (jd_text_input or "").strip()
                # Validate content safety
                is_safe, safety_error = validate_content_safety(job_text)
                if not is_safe:
                    st.error(f"🚫 {safety_error}")
                    return

            elif jd_mode == "Upload PDF":
                if not jd_pdf_file:
                    st.error("Please upload a job description PDF.")
                    return

                # Validate file
                filename = sanitize_filename(jd_pdf_file.name)
                if not validate_file_extension(filename):
                    st.error("🚫 Invalid file type. Only PDF files are allowed.")
                    log_security_event('INVALID_FILE_TYPE', {'filename': filename})
                    return

                file_bytes = jd_pdf_file.read()
                if not validate_file_size(file_bytes, SecurityConfig.MAX_JD_SIZE):
                    st.error(f"🚫 File too large. Maximum size is {SecurityConfig.MAX_JD_SIZE / 1024 / 1024:.0f}MB.")
                    return

                try:
                    job_text = extract_text_from_pdf(file_bytes)
                except RuntimeError as e:
                    st.error(f"Failed to read PDF: {str(e)}")
                    return

            elif jd_mode == "Job URL":
                if not jd_url_input:
                    st.error("Please provide a job posting URL.")
                    return

                # Validate and sanitize URL
                safe_url = sanitize_url(jd_url_input.strip())
                if not safe_url:
                    st.error("🚫 Invalid or unsafe URL. Please use HTTPS URLs only.")
                    return

                try:
                    job_text = fetch_text_from_url(safe_url)
                except RuntimeError as e:
                    st.error(f"Failed to fetch URL: {str(e)}")
                    return

            # Validate job description
            if not job_text or len(job_text.strip()) < 200:
                st.error("The job description looks very short or is missing. Please provide the full job description.")
                return

            is_safe, safety_error = validate_content_safety(job_text)
            if not is_safe:
                st.error(f"🚫 {safety_error}")
                return

            # Validate resume file
            if not resume_file:
                st.error("Please upload your resume as a PDF.")
                return

            # Validate resume file
            resume_filename = sanitize_filename(resume_file.name)
            if not validate_file_extension(resume_filename):
                st.error("🚫 Invalid file type. Only PDF files are allowed.")
                log_security_event('INVALID_FILE_TYPE', {'filename': resume_filename})
                return

            resume_bytes = resume_file.read()
            if not validate_file_size(resume_bytes, SecurityConfig.MAX_RESUME_SIZE):
                st.error(f"🚫 Resume file too large. Maximum size is {SecurityConfig.MAX_RESUME_SIZE / 1024 / 1024:.0f}MB.")
                return

            # Extract resume text
            try:
                resume_text = extract_text_from_pdf(resume_bytes)
            except RuntimeError as e:
                st.error(str(e))
                return

            # Validate resume content
            is_safe, safety_error = validate_content_safety(resume_text)
            if not is_safe:
                st.error(f"🚫 {safety_error}")
                return

            all_text_parts = [resume_text]

            # LinkedIn profile (optional, best-effort, public only)
            linkedin_text = ""
            if linkedin_url_sidebar and linkedin_url_sidebar.strip():
                safe_linkedin_url = sanitize_url(linkedin_url_sidebar.strip())
                if safe_linkedin_url:
                    try:
                        linkedin_text = get_linkedin_profile_text(safe_linkedin_url)
                        if linkedin_text:
                            # Validate LinkedIn content
                            is_safe, _ = validate_content_safety(linkedin_text)
                            if is_safe:
                                all_text_parts.append(linkedin_text)
                            else:
                                linkedin_text = ""  # Ignore if unsafe
                    except Exception:
                        linkedin_text = ""  # Silently fail for optional LinkedIn
                else:
                    st.warning("LinkedIn URL appears unsafe - skipping LinkedIn profile.")

            combined_resume_text = "\n\n".join(t for t in all_text_parts if t and t.strip())

            if not combined_resume_text or len(combined_resume_text.strip()) < 200:
                st.warning(
                    "The text from your resume could not be fully extracted. "
                    "ATS systems may also struggle with this file. Consider exporting a simpler PDF."
                )

            posting_date_str = posting_date.isoformat() if posting_date else ""

            # Log processing activity (GDPR audit)
            data_categories = ['resume', 'job_description']
            if linkedin_text:
                data_categories.append('linkedin_profile')

            AuditLog.log_processing_activity(
                'ATS_ANALYSIS_STARTED',
                st.session_state.session_id,
                data_categories
            )

            breakdown = score_resume_against_job(
                jd_text=job_text,
                resume_text=combined_resume_text,
                posting_date_str=posting_date_str,
            )

            # Store in session state for resume generation
            st.session_state.job_text = job_text
            st.session_state.resume_text = resume_text
            st.session_state.linkedin_text = linkedin_text
            st.session_state.combined_resume_text = combined_resume_text
            st.session_state.breakdown = breakdown
            st.session_state.analysis_complete = True

            # Log completion
            AuditLog.log_processing_activity(
                'ATS_ANALYSIS_COMPLETED',
                st.session_state.session_id,
                data_categories
            )

    # Display results if analysis has been completed
    if st.session_state.get("analysis_complete", False):
        breakdown = st.session_state.breakdown

        # Layout: left = scores, right = recommendations
        left, right = st.columns([1, 1])

        with left:
            st.subheader("Match score (ATS-style)")
            st.metric("Overall match", f"{breakdown.overall:.1f} / 100")

            st.markdown("#### Sub-scores")
            st.progress(
                int(min(breakdown.keyword_similarity, 100)),
                text=f"Keyword relevance: {breakdown.keyword_similarity:.1f}%",
            )
            st.progress(
                int(min(breakdown.skills_coverage, 100)),
                text=f"Skills coverage: {breakdown.skills_coverage:.1f}%",
            )
            st.progress(
                int(min(breakdown.seniority_alignment, 100)),
                text=f"Seniority alignment: {breakdown.seniority_alignment:.1f}%",
            )
            st.progress(
                int(min(breakdown.ats_friendliness, 100)),
                text=f"ATS-friendliness: {breakdown.ats_friendliness:.1f}%",
            )

            st.caption(
                f"Posting recency factor: {breakdown.posting_recency_factor:.1f}%. {breakdown.recency_explanation}"
            )

        with right:
            st.subheader("🎯 Actionable Steps to Improve Your Match")

            # Generate actionable steps
            job_text = st.session_state.job_text
            resume_text = st.session_state.resume_text
            linkedin_text = st.session_state.get('linkedin_text', '')
            action_steps = generate_actionable_steps(breakdown, job_text, resume_text, linkedin_text)

            # Display score interpretation first
            if breakdown.overall >= 80:
                st.success("✅ **Strong Match** - Your resume should perform well in ATS. Focus on fine-tuning.")
            elif breakdown.overall >= 60:
                st.warning("⚠️ **Decent Match** - Improvements recommended before applying. Address critical items below.")
            else:
                st.error("❌ **Weak Match** - Significant improvements needed. Consider if this role truly fits your background.")

            st.markdown("---")

            # Display actionable steps with priority ordering
            for idx, step in enumerate(action_steps, 1):
                with st.expander(f"**{step['priority']}** - {step['category']}: {step['action']}", expanded=(idx <= 2)):
                    st.markdown(f"**What to do:**")
                    for detail in step['details']:
                        st.markdown(f"• {detail}")
                    st.markdown(f"**Expected Impact:** {step['impact']}")

            st.markdown("---")

            # Show matched keywords for reference
            if breakdown.matched_keywords:
                with st.expander("✅ Keywords you're already covering well"):
                    st.write(", ".join(sorted(set(breakdown.matched_keywords))))
                    st.caption("Keep these prominent in your resume!")

            st.markdown("---")

            # Strategic guidance
            st.markdown("#### 📋 Application Strategy")
            if breakdown.overall >= 80:
                st.markdown(
                    "• **Apply confidently** - Your resume should pass ATS filters\n"
                    "• **Apply early** - Fresh applications get more attention\n"
                    "• **Network** - Reach out to the hiring manager or employees on LinkedIn\n"
                    "• **Customize further** - Tailor your summary to mention this specific company"
                )
            elif breakdown.overall >= 60:
                st.markdown(
                    "• **Improve first** - Address the critical items above before applying\n"
                    "• **Test your changes** - Re-run this analysis after making updates\n"
                    "• **Consider applying** - If improvements bring you to 75+%, you have a decent shot\n"
                    "• **Network** - A referral can help overcome a moderate ATS score"
                )
            else:
                st.markdown(
                    "• **Major revision needed** - Address all critical and high-priority items\n"
                    "• **Assess fit** - Honestly evaluate if your background matches the role requirements\n"
                    "• **Seek referrals** - ATS alone likely won't get you through; you need an internal advocate\n"
                    "• **Consider similar roles** - Look for positions that better match your current experience"
                )

            st.markdown("---")
            st.caption("💡 **Pro tip:** Each 10-point improvement in your score significantly increases your chances of getting past ATS filters and landing an interview.")


if __name__ == "__main__":
    main()


