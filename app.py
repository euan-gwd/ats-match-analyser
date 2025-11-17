import io
from datetime import date
from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup
from pypdf import PdfReader

from ats_scoring import score_resume_against_job
from resume_optimizer import build_optimized_resume, build_optimized_resume_docx


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
        linkedin_has_better_metrics = False
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
        'linkedin_has_metrics': linkedin_has_better_metrics if linkedin_lower else False
    }


def generate_actionable_steps(breakdown, job_text: str, resume_text: str, linkedin_text: str = "") -> list[dict]:
    """Generate specific, actionable changes based on actual job description and resume analysis."""
    steps = []

    # Extract actual content from JD and CV
    jd_analysis = _extract_job_phrases(job_text)
    gap_analysis = _analyze_resume_gaps(job_text, resume_text, breakdown.missing_keywords, linkedin_text)

    # CRITICAL: Missing keywords that are in JD requirements
    if breakdown.skills_coverage < 70 and gap_analysis['missing_critical']:
        specific_actions = []

        for keyword in gap_analysis['missing_critical'][:5]:
            # Find context in JD where this keyword appears
            import re
            jd_lower = job_text.lower()
            keyword_context = re.search(rf'([^.!?]*{re.escape(keyword)}[^.!?]*)[.!?]', jd_lower)
            context_hint = keyword_context.group(1).strip()[:80] if keyword_context else ""

            if context_hint:
                specific_actions.append(f'**"{keyword}"** - The JD mentions: "{context_hint}..." → Add this to your Skills section and mention it in a relevant project/role')
            else:
                specific_actions.append(f'**"{keyword}"** → Add to Skills section and describe where you used it')

        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Missing Required Keywords",
            "action": f"Add these {len(gap_analysis['missing_critical'][:5])} critical keywords from the job requirements",
            "details": specific_actions,
            "impact": f"Skills Coverage: {breakdown.skills_coverage:.0f}% → ~{min(90, breakdown.skills_coverage + 25):.0f}%"
        })

    # CRITICAL: LinkedIn content that should be in CV
    if gap_analysis['linkedin_additions']:
        linkedin_actions = []
        linkedin_actions.append("🔗 **Your LinkedIn has relevant content missing from your CV:**")

        for item in gap_analysis['linkedin_additions'][:5]:
            keyword = item['keyword']
            context = item['context']
            linkedin_actions.append(f'**"{keyword}"** - Your LinkedIn mentions: "{context}" → **COPY this to your CV** (relevant to the JD)')

        if len(gap_analysis['linkedin_additions']) > 5:
            linkedin_actions.append(f"Plus {len(gap_analysis['linkedin_additions']) - 5} more keywords from your LinkedIn that match the JD")

        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Transfer from LinkedIn",
            "action": "Move these relevant experiences from LinkedIn to your CV",
            "details": linkedin_actions,
            "impact": f"Quick win - this content already exists on your profile! Could add {len(gap_analysis['linkedin_additions'])} missing keywords"
        })

    # CRITICAL: Mirror specific language from JD
    if breakdown.keyword_similarity < 70 and gap_analysis['key_phrases']:
        phrase_actions = []
        for phrase in gap_analysis['key_phrases'][:4]:
            phrase_actions.append(f'Use phrase: **"{phrase}"** (appears multiple times in JD but missing in your resume)')

        if jd_analysis['role_title']:
            phrase_actions.insert(0, f'Start your summary with: "**{jd_analysis["role_title"]}** with expertise in..." matching the exact job title')

        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Language Alignment",
            "action": "Mirror these exact phrases from the job description",
            "details": phrase_actions,
            "impact": f"Keyword Relevance: {breakdown.keyword_similarity:.0f}% → ~{min(90, breakdown.keyword_similarity + 20):.0f}%"
        })

    # HIGH: Add/improve professional summary
    if not gap_analysis['has_summary'] or breakdown.keyword_similarity < 75:
        summary_bullets = []
        if jd_analysis['role_title']:
            summary_bullets.append(f'Add opening: "**{jd_analysis["role_title"]}** with [X] years of experience in [top 3 skills from JD]"')
        if jd_analysis['required_years']:
            summary_bullets.append(f'Explicitly state: "**{jd_analysis["required_years"]}+ years** of hands-on experience" (the JD requires this)')

        # Add top 3 missing keywords to summary recommendation
        if breakdown.missing_keywords[:3]:
            summary_bullets.append(f'Include these keywords: **{", ".join(breakdown.missing_keywords[:3])}**')

        if not gap_analysis['has_summary']:
            summary_bullets.insert(0, '**CREATE a Professional Summary** section at the top of your resume (currently missing)')

        steps.append({
            "priority": "🟡 HIGH",
            "category": "Professional Summary",
            "action": "Add/rewrite your professional summary to match job requirements",
            "details": summary_bullets if summary_bullets else ["Rewrite summary to include top keywords and exact role title"],
            "impact": "Immediate ATS ranking boost - summary is scanned first"
        })

    # HIGH: ATS formatting issues
    if breakdown.ats_friendliness < 80 and breakdown.ats_reasons:
        steps.append({
            "priority": "🟡 HIGH",
            "category": "ATS Formatting",
            "action": "Fix these formatting issues blocking ATS parsing",
            "details": [f"**FIX:** {reason}" for reason in breakdown.ats_reasons],
            "impact": f"ATS-Friendliness: {breakdown.ats_friendliness:.0f}% → ~95%"
        })

    # HIGH: Quantify achievements
    if not gap_analysis['has_metrics']:
        metrics_actions = [
            "**REWRITE** at least 3 bullet points with numbers: '% improvement', '$ saved', '# of users', 'team size'",
            "Example: Change 'Led development projects' → 'Led **5-person team** delivering **3 major projects**, improving efficiency by **40%**'",
            "Example: Change 'Improved system performance' → 'Optimized database queries, reducing load time by **60%** for **10K+ daily users**'",
        ]

        if gap_analysis.get('linkedin_has_metrics'):
            metrics_actions.insert(0, "🔗 **Your LinkedIn profile has quantified achievements - transfer those metrics to your CV!**")

        steps.append({
            "priority": "🟡 HIGH",
            "category": "Quantified Impact",
            "action": "Add metrics to your achievements (currently missing)",
            "details": metrics_actions,
            "impact": "Major boost - quantified achievements score 3x higher in ATS ranking"
        })

    # MEDIUM: Seniority alignment
    if breakdown.seniority_alignment < 80:
        seniority_actions = [breakdown.seniority_explanation]

        if jd_analysis['required_years']:
            years_statement = f'Add to summary: "**{jd_analysis["required_years"]}+ years** of [field] experience"'
            seniority_actions.append(years_statement)

        # Check if using action verbs appropriate for seniority
        jd_lower = job_text.lower()
        if any(word in jd_lower for word in ['lead', 'senior', 'principal']):
            seniority_actions.append('**USE** senior-level action verbs: "Architected", "Led", "Mentored", "Drove", "Established"')
            seniority_actions.append('**QUANTIFY** scope: team sizes, budget responsibility, strategic impact')

        steps.append({
            "priority": "🟡 MEDIUM",
            "category": "Seniority Match",
            "action": "Adjust seniority signals",
            "details": seniority_actions,
            "impact": f"Seniority Alignment: {breakdown.seniority_alignment:.0f}% → ~{min(95, breakdown.seniority_alignment + 15):.0f}%"
        })

    # OPTIMIZATION: Already strong - fine-tune
    if breakdown.skills_coverage >= 70 and breakdown.keyword_similarity >= 70:
        optimize_actions = [
            f"**ADD** these additional matched keywords throughout: {', '.join(breakdown.matched_keywords[:5])}",
            "**REORDER** your experience - put most relevant role first, even if not most recent",
        ]

        if breakdown.missing_keywords[5:10]:
            optimize_actions.append(f'**INCLUDE** secondary keywords: {", ".join(breakdown.missing_keywords[5:10])}')

        steps.append({
            "priority": "🟢 OPTIMIZE",
            "category": "Fine-Tuning",
            "action": "Polish your strong resume further",
            "details": optimize_actions,
            "impact": f"Push from {breakdown.overall:.0f} → 90+ score"
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

    st.title("📄 ATS Match Analyzer")
    st.markdown(
        "Evaluate how your resume is likely to perform in a modern ATS against a specific job posting."
    )

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
        # Clear previous generation state
        st.session_state.docx_generated = False
        st.session_state.text_generated = False

        with st.spinner("Parsing documents and emulating ATS scoring..."):
            # Basic validation
            job_text = get_job_description_text(jd_mode, jd_text_input, jd_pdf_file, jd_url_input)
            if not job_text or len(job_text.strip()) < 200:
                st.error(
                    "The job description looks very short or is missing. Please provide the full job description."
                )
                return

            if not resume_file:
                st.error("Please upload your resume as a PDF.")
                return

            # Resume + optional LinkedIn text
            try:
                resume_text = extract_text_from_pdf(resume_file.read())
            except RuntimeError as e:
                st.error(str(e))
                return

            all_text_parts = [resume_text]

            # LinkedIn profile (best-effort, public only)
            linkedin_text = get_linkedin_profile_text(linkedin_url_sidebar.strip() or None)
            if linkedin_text:
                all_text_parts.append(linkedin_text)

            combined_resume_text = "\n\n".join(t for t in all_text_parts if t and t.strip())

            if not combined_resume_text or len(combined_resume_text.strip()) < 200:
                st.warning(
                    "The text from your resume could not be fully extracted. "
                    "ATS systems may also struggle with this file. Consider exporting a simpler PDF."
                )

            posting_date_str = posting_date.isoformat() if posting_date else ""

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


