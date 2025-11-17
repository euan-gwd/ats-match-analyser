import io
from datetime import date
from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup
from pypdf import PdfReader

from ats_scoring import score_resume_against_job
from resume_optimizer import build_optimized_resume, build_optimized_resume_docx


def generate_actionable_steps(breakdown, job_text: str, resume_text: str) -> list[dict]:
    """Generate prioritized, actionable steps to improve the resume."""
    steps = []

    # Priority 1: Critical missing keywords (if skills coverage is low)
    if breakdown.skills_coverage < 70 and breakdown.missing_keywords:
        top_missing = breakdown.missing_keywords[:10]
        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Missing Keywords",
            "action": f"Add these high-impact keywords where truthful: {', '.join(top_missing[:5])}",
            "details": [
                f"Review the job description and identify where you've used these skills",
                f"Add them to your Skills section if you have genuine experience",
                f"Incorporate them into bullet points describing relevant projects or achievements",
                f"Don't just list them - show how you used them with specific examples"
            ],
            "impact": f"Could improve Skills Coverage from {breakdown.skills_coverage:.0f}% to ~{min(90, breakdown.skills_coverage + 20):.0f}%"
        })

    # Priority 2: Keyword density/relevance (if similarity is low)
    if breakdown.keyword_similarity < 70:
        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Keyword Relevance",
            "action": "Mirror the job description's language more closely",
            "details": [
                "Use the same terminology the job posting uses (e.g., if they say 'stakeholder engagement', don't say 'client communication')",
                "Rewrite your professional summary to mention the exact role title and key requirements",
                "Adjust your experience bullets to emphasize responsibilities that match the job description",
                "Use industry-specific terms and phrases from the posting"
            ],
            "impact": f"Could improve Keyword Relevance from {breakdown.keyword_similarity:.0f}% to ~{min(90, breakdown.keyword_similarity + 25):.0f}%"
        })

    # Priority 3: ATS formatting issues
    if breakdown.ats_friendliness < 80 and breakdown.ats_reasons:
        steps.append({
            "priority": "🟡 HIGH",
            "category": "ATS Formatting",
            "action": "Fix resume formatting for better ATS parsing",
            "details": breakdown.ats_reasons + [
                "Use a simple, single-column layout",
                "Save as PDF from Word/Google Docs (not from design tools)",
                "Use standard section headings: 'Experience', 'Education', 'Skills'",
                "Avoid headers/footers, text boxes, tables, and graphics"
            ],
            "impact": f"Could improve ATS-Friendliness from {breakdown.ats_friendliness:.0f}% to ~95%"
        })

    # Priority 4: Seniority alignment issues
    if breakdown.seniority_alignment < 80:
        steps.append({
            "priority": "🟡 HIGH",
            "category": "Seniority Alignment",
            "action": "Address seniority level mismatch",
            "details": [
                breakdown.seniority_explanation,
                "Add a 'X+ years of experience in [field]' statement in your summary",
                "Use seniority indicators: for senior roles, emphasize leadership, mentoring, and strategic impact",
                "Quantify your achievements with metrics and scope (team size, budget, users impacted)",
                "If underqualified, highlight transferable skills and rapid learning ability"
            ],
            "impact": f"Could improve Seniority Alignment from {breakdown.seniority_alignment:.0f}% to ~{min(95, breakdown.seniority_alignment + 20):.0f}%"
        })

    # Additional optimization opportunities
    if breakdown.skills_coverage >= 70 and breakdown.keyword_similarity >= 70:
        steps.append({
            "priority": "🟢 OPTIMIZATION",
            "category": "Fine-Tuning",
            "action": "Polish your already-strong resume",
            "details": [
                "Add more matched keywords in context throughout your resume",
                "Ensure your most relevant experience is in the top 1/3 of your resume",
                "Add quantified achievements (increased X by Y%, reduced Z by N hours)",
                "Include relevant certifications or training if you have them",
                "Customize your professional summary to mention this specific company/role"
            ],
            "impact": "Could push your score from good to excellent (90+%)"
        })

    # Additional missing keywords if space for improvement
    if breakdown.missing_keywords and len(breakdown.missing_keywords) > 10:
        remaining = breakdown.missing_keywords[10:20]
        if remaining:
            steps.append({
                "priority": "🟢 OPTIMIZATION",
                "category": "Additional Keywords",
                "action": f"Consider these secondary keywords: {', '.join(remaining[:5])}",
                "details": [
                    "These appeared in the job description but with less emphasis",
                    "Add them if you have genuine experience, especially in a 'Technical Skills' or 'Tools' section",
                    "Include them in project descriptions where relevant"
                ],
                "impact": "Marginal improvement, but could help in keyword-filtered searches"
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
            resume_text = st.session_state.combined_resume_text
            action_steps = generate_actionable_steps(breakdown, job_text, resume_text)

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


