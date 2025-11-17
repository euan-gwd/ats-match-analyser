"""FastAPI Backend for ATS Match Analyser."""
import io
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from app.core.ats_scoring import score_resume_against_job
from app.core.security_utils import (
    validate_file_upload,
    sanitize_url,
    validate_content_safety,
    check_rate_limit,
    validate_session_timeout,
    scrub_pii_from_logs
)
from app.core.gdpr_compliance import GDPRCompliance

# Import the actionable steps generator from the parent directory
import sys
from pathlib import Path
# Add parent directory to path to import from root app.py
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

try:
    from app import generate_actionable_steps
except ImportError:
    # If import fails, create a simple placeholder
    def generate_actionable_steps(breakdown, job_text, resume_text, linkedin_text=""):
        return []

# Initialize FastAPI app
app = FastAPI(
    title="ATS Match Analyser API",
    description="AI-powered CV optimization against job descriptions",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # Vite ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
gdpr = GDPRCompliance()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
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
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")


def fetch_text_from_url(url: str) -> str:
    """Fetch text content from URL."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.find("main") or soup.find("article")
    if main:
        return main.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ATS Match Analyser API"}


@app.get("/api/privacy-notice")
async def get_privacy_notice():
    """Get GDPR privacy notice."""
    return {"notice": gdpr.get_privacy_notice()}


@app.post("/api/consent")
async def record_consent(session_id: str = Form(...)):
    """Record user consent."""
    gdpr.record_consent(session_id)
    return {"status": "consent_recorded", "session_id": session_id}


@app.post("/api/analyze")
async def analyze_cv(
    cv_file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    job_url: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    session_id: str = Form(...),
):
    """
    Analyze CV against job description.

    Args:
        cv_file: PDF file of the CV
        job_description: Job description text (optional if job_url provided)
        job_url: URL to job posting (optional if job_description provided)
        linkedin_url: LinkedIn profile URL (optional)
        session_id: Session ID for tracking
    """
    # Security checks
    if not check_rate_limit(session_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait before submitting again.")

    if not validate_session_timeout(session_id):
        raise HTTPException(status_code=401, detail="Session expired. Please refresh and try again.")

    # Validate CV file
    cv_bytes = await cv_file.read()
    if not validate_file_upload(cv_bytes, cv_file.filename):
        raise HTTPException(status_code=400, detail="Invalid CV file. Please upload a PDF under 5MB.")

    # Extract CV text
    try:
        cv_text = extract_text_from_pdf(cv_bytes)
        if not validate_content_safety(cv_text):
            raise HTTPException(status_code=400, detail="CV content failed safety validation.")
    except Exception as e:
        scrub_pii_from_logs(str(e))
        raise HTTPException(status_code=400, detail="Failed to process CV file.")

    # Get job description
    jd_text = ""
    if job_description:
        if not validate_content_safety(job_description):
            raise HTTPException(status_code=400, detail="Job description content failed safety validation.")
        jd_text = job_description
    elif job_url:
        sanitized_url = sanitize_url(job_url)
        if not sanitized_url:
            raise HTTPException(status_code=400, detail="Invalid job URL.")
        try:
            jd_text = fetch_text_from_url(sanitized_url)
            if not validate_content_safety(jd_text):
                raise HTTPException(status_code=400, detail="Job posting content failed safety validation.")
        except HTTPException:
            raise
        except Exception as e:
            scrub_pii_from_logs(str(e))
            raise HTTPException(status_code=400, detail="Failed to fetch job posting.")
    else:
        raise HTTPException(status_code=400, detail="Either job_description or job_url must be provided.")

    # Get LinkedIn profile (optional)
    linkedin_text = ""
    if linkedin_url:
        sanitized_linkedin = sanitize_url(linkedin_url)
        if sanitized_linkedin and "linkedin.com" in sanitized_linkedin:
            try:
                linkedin_text = fetch_text_from_url(sanitized_linkedin)
            except:
                linkedin_text = ""  # LinkedIn is optional

    # Run ATS analysis
    try:
        # Order: (job_description, resume_text). Do not pass linkedin here.
        breakdown = score_resume_against_job(jd_text, cv_text)

        # Generate actionable steps
        actionable_steps = generate_actionable_steps(breakdown, jd_text, cv_text, linkedin_text)

        # Log analysis (with PII scrubbed)
        gdpr.log_analysis(session_id, {
            "overall_score": breakdown.overall,
            "timestamp": datetime.now().isoformat()
        })

        # Convert breakdown to dict
        result = {
            "overall": breakdown.overall,
            "keyword_similarity": breakdown.keyword_similarity,
            "skills_coverage": breakdown.skills_coverage,
            "seniority_alignment": breakdown.seniority_alignment,
            "ats_friendliness": breakdown.ats_friendliness,
            "matched_keywords": breakdown.matched_keywords,
            "missing_keywords": breakdown.missing_keywords,
            "seniority_explanation": breakdown.seniority_explanation,
            "ats_reasons": breakdown.ats_reasons,
            "actionable_steps": actionable_steps
        }

        return JSONResponse(content=result)

    except Exception as e:
        scrub_pii_from_logs(str(e))
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")


@app.post("/api/export-data")
async def export_user_data(session_id: str = Form(...)):
    """Export user data (GDPR compliance)."""
    data = gdpr.export_user_data(session_id)
    return JSONResponse(content=data)


@app.delete("/api/delete-data")
async def delete_user_data(session_id: str = Form(...)):
    """Delete user data (GDPR compliance)."""
    gdpr.delete_user_data(session_id)
    return {"status": "deleted", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
