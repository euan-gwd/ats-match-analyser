import io
from datetime import date
from typing import Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup
from pypdf import PdfReader

from ats_scoring import score_resume_against_job
from resume_optimizer import build_optimized_resume, build_optimized_resume_docx


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
            ("Job URL", "Paste text", "Upload PDF"),
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

        st.header("Additional sources (optional)")
        st.caption(
            "You can provide extra documents or a public LinkedIn profile. "
            "Content from these will be merged with your resume text for scoring and optimization, "
            "but **no new facts will be invented**."
        )
        extra_docs = st.file_uploader(
            "Additional supporting documents (PDFs)",
            type=["pdf"],
            accept_multiple_files=True,
        )
        linkedin_url_sidebar = st.text_input(
            "Public LinkedIn profile URL (optional)",
            placeholder="https://www.linkedin.com/in/your-profile",
        )

        analyze_button = st.button("Analyze match", type="primary")

    # Main content area
    if analyze_button:
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

            # Resume + optional extra documents + LinkedIn text
            try:
                resume_text = extract_text_from_pdf(resume_file.read())
            except RuntimeError as e:
                st.error(str(e))
                return

            all_text_parts = [resume_text]

            # Extra PDFs
            if extra_docs:
                for f in extra_docs:
                    try:
                        extra_text = extract_text_from_pdf(f.read())
                    except RuntimeError:
                        continue
                    if extra_text:
                        all_text_parts.append(extra_text)

            # LinkedIn profile (best-effort, public only)
            linkedin_text = get_linkedin_profile_text(linkedin_url_sidebar.strip() or None)
            if linkedin_text:
                all_text_parts.append(linkedin_text)

            combined_resume_text = "\n\n".join(t for t in all_text_parts if t and t.strip())

            if not combined_resume_text or len(combined_resume_text.strip()) < 200:
                st.warning(
                    "The combined text from your resume and additional sources is very short or could not be fully extracted. "
                    "ATS systems may also struggle with these files. Consider exporting simpler PDFs."
                )

            posting_date_str = posting_date.isoformat() if posting_date else ""

            breakdown = score_resume_against_job(
                jd_text=job_text,
                resume_text=combined_resume_text,
                posting_date_str=posting_date_str,
            )

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
            st.subheader("Recommendations (as if from a recruiter using ATS search)")

            st.markdown("##### 1. High-impact keywords and skills")
            if breakdown.missing_keywords:
                st.write(
                    "These job-specific terms are **important in the description but missing or under-emphasized in your resume**. "
                    "Where genuinely true, weave them into your experience bullets, skills section, and summary:"
                )
                st.write(", ".join(sorted(set(breakdown.missing_keywords))))
            else:
                st.write(
                    "Your resume already covers most of the high-value keywords and skills from this job description."
                )

            if breakdown.matched_keywords:
                with st.expander("Keywords you're already covering well"):
                    st.write(", ".join(sorted(set(breakdown.matched_keywords))))

            st.markdown("##### 2. Seniority & fit signals")
            st.write(breakdown.seniority_explanation)
            st.write(
                "If ATS filters are set to narrow bands (e.g., '3–5 years experience' or 'Senior'), "
                "consider explicitly stating your years of experience and level in your summary."
            )

            st.markdown("##### 3. ATS-friendly formatting")
            if breakdown.ats_reasons:
                st.write(
                    "These formatting issues can reduce how well ATS parsers understand your resume. "
                    "Fixing them can boost your visibility even if your experience stays the same:"
                )
                for r in breakdown.ats_reasons:
                    st.markdown(f"- {r}")
            else:
                st.write(
                    "Your resume looks structurally ATS-friendly based on common parsing heuristics."
                )

            st.markdown("##### 4. How to use this score strategically")
            st.write(
                "- **80–100**: Strong match. Tailor a few bullets, apply early, and consider reaching out to the hiring manager or recruiter.\n"
                "- **60–79**: Decent match. Improve missing keywords/skills first, then apply.\n"
                "- **<60**: Weak ATS match. You may still apply, but expect low visibility unless you have a strong referral or can substantially tailor your resume."
            )

            st.markdown("##### 5. Generate ATS-optimized resume (no new facts)")
            st.write(
                "This creates a fully formatted resume that rearranges and emphasizes information that is **already in your resume** to maximize ATS score. "
                "It does **not** add new experience, skills, or dates. Available as editable Word document or text."
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📄 Generate Word Document (.docx)", type="primary"):
                    with st.spinner("Creating ATS-optimized Word document..."):
                        docx_buffer = build_optimized_resume_docx(
                            jd_text=job_text,
                            resume_text=combined_resume_text,
                            breakdown=breakdown,
                        )
                        st.success("✅ Optimized resume created!")
                        st.download_button(
                            "⬇️ Download Word Document",
                            data=docx_buffer.getvalue(),
                            file_name="optimized_resume_ats.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                        st.info(
                            "💡 **Tip**: Open in Microsoft Word or Google Docs to edit. "
                            "The document is formatted for maximum ATS compatibility with clear sections and keyword emphasis."
                        )

            with col2:
                if st.button("📝 Generate Text Version"):
                    optimized_text = build_optimized_resume(
                        jd_text=job_text,
                        resume_text=combined_resume_text,
                        breakdown=breakdown,
                    )
                    st.text_area(
                        "Optimized resume draft (copy and adapt as needed)",
                        optimized_text,
                        height=400,
                    )
                    st.download_button(
                        "Download as .txt",
                        data=optimized_text,
                        file_name="optimized_resume.txt",
                        mime="text/plain",
                    )


if __name__ == "__main__":
    main()


