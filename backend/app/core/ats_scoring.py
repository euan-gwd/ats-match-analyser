import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from dateutil.parser import parse as parse_date
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SECTION_HEADERS = [
    "experience",
    "work experience",
    "professional experience",
    "employment history",
    "education",
    "skills",
    "technical skills",
    "projects",
    "certifications",
    "summary",
    "profile",
]

COMMON_SKILLS = [
    # Technical / software
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "react",
    "angular",
    "vue",
    "node",
    "node.js",
    "django",
    "flask",
    "spring",
    "kotlin",
    "swift",
    "sql",
    "nosql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "graphql",
    "rest",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "terraform",
    "ansible",
    "linux",
    "git",
    "ci/cd",
    "jenkins",
    "circleci",
    "pytest",
    "unit testing",
    "integration testing",
    # Data / analytics
    "pandas",
    "numpy",
    "scikit-learn",
    "machine learning",
    "deep learning",
    "data analysis",
    "data science",
    "power bi",
    "tableau",
    "excel",
    "statistics",
    # Business / soft skills
    "project management",
    "product management",
    "stakeholder management",
    "communication",
    "leadership",
    "mentoring",
    "teamwork",
    "collaboration",
    "agile",
    "scrum",
    "kanban",
]

SENIORITY_KEYWORDS = {
    "intern": ["intern", "internship"],
    "junior": ["junior", "entry level", "graduate"],
    "mid": ["mid-level", "mid level"],
    "senior": ["senior", "sr.", "sr ", "staff"],
    "lead": ["lead", "principal"],
    "manager": ["manager", "head of", "director"],
}


def _normalize(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_keywords(text: str, top_k: int = 30) -> List[str]:
    """
    Rough keyword extraction using TF-IDF on a single document.
    """
    normalized = _normalize(text)
    if not normalized:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=256,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform([normalized])
    except ValueError:
        return []

    scores = tfidf_matrix.toarray()[0]
    indices = np.argsort(scores)[::-1][:top_k]
    feature_names = np.array(vectorizer.get_feature_names_out())
    return [feature_names[i] for i in indices if scores[i] > 0]


def _cosine_similarity(jd_text: str, resume_text: str) -> float:
    jd = _normalize(jd_text)
    cv = _normalize(resume_text)
    if not jd or not cv:
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        tfidf = vectorizer.fit_transform([jd, cv])
    except ValueError:
        return 0.0

    sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return float(sim)


def _skills_coverage(jd_text: str, resume_text: str) -> Tuple[float, List[str], List[str]]:
    jd = _normalize(jd_text)
    cv = _normalize(resume_text)
    if not jd or not cv:
        return 0.0, [], []

    jd_tokens = set(re.findall(r"[a-zA-Z\+\#\.]{2,}", jd))
    cv_tokens = set(re.findall(r"[a-zA-Z\+\#\.]{2,}", cv))

    jd_skills = {s for s in COMMON_SKILLS if any(tok in jd for tok in s.split())}
    cv_skills = {s for s in COMMON_SKILLS if any(tok in cv for tok in s.split())}

    # Also consider any JD tokens that appear multiple times as "implicit" skills
    important_jd_terms = set(_extract_keywords(jd_text, top_k=40))

    matched_from_skills = jd_skills & cv_skills
    matched_from_terms = {t for t in important_jd_terms if t in cv}

    # Required set is union of explicit skills and important terms
    required = jd_skills | important_jd_terms
    if not required:
        return 0.0, [], []

    matched = (matched_from_skills | matched_from_terms) & required
    coverage = len(matched) / len(required)

    missing = sorted(list(required - matched))
    matched_list = sorted(list(matched))

    return float(coverage), matched_list, missing


def _detect_seniority(text: str) -> str:
    t = _normalize(text)
    for level, keywords in SENIORITY_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return level
    return "unspecified"


def _estimate_years_experience(text: str) -> float:
    """
    Very rough heuristic: look for patterns like "X years" or "X+ years".
    """
    t = _normalize(text)
    matches = re.findall(r"(\d+)\+?\s+years", t)
    if not matches:
        return 0.0
    years = [int(m) for m in matches]
    return float(max(years))


def _seniority_alignment(jd_text: str, resume_text: str) -> Tuple[float, str]:
    jd_level = _detect_seniority(jd_text)
    cv_level = _detect_seniority(resume_text)
    jd_years = _estimate_years_experience(jd_text)
    cv_years = _estimate_years_experience(resume_text)

    explanation_parts = []

    # Map levels to an ordinal scale
    order = {
        "intern": 0,
        "junior": 1,
        "mid": 2,
        "senior": 3,
        "lead": 4,
        "manager": 5,
        "unspecified": 2,  # treat unspecified as mid
    }

    jd_ord = order.get(jd_level, 2)
    cv_ord = order.get(cv_level, 2)

    diff = cv_ord - jd_ord
    if diff == 0:
        level_score = 1.0
        explanation_parts.append("Seniority level looks well aligned with the job description.")
    elif diff == -1:
        level_score = 0.85
        explanation_parts.append("Resume is slightly more junior than the job; highlight impact and ownership.")
    elif diff <= -2:
        level_score = 0.6
        explanation_parts.append("Resume appears significantly more junior than the role; you may be screened out.")
    elif diff == 1:
        level_score = 0.9
        explanation_parts.append("Resume is slightly more senior; might be acceptable but ensure relevance.")
    else:
        level_score = 0.8
        explanation_parts.append("Resume is considerably more senior; ATS may still match but recruiter fit is uncertain.")

    # Years of experience consistency check
    if jd_years and cv_years:
        if cv_years + 1 < jd_years:
            level_score *= 0.8
            explanation_parts.append(
                f"Job seems to expect around {jd_years:.0f}+ years; resume signals about {cv_years:.0f}."
            )
        elif cv_years >= jd_years:
            explanation_parts.append(
                f"Years of experience ({cv_years:.0f}+) seem sufficient for the role ({jd_years:.0f}+)."
            )

    explanation = " ".join(explanation_parts) if explanation_parts else "Seniority alignment is unclear."
    return float(max(0.0, min(1.0, level_score))), explanation


def _ats_friendliness(resume_text: str) -> Tuple[float, List[str]]:
    """
    Heuristic ATS-friendliness score based on formatting and structure cues.
    """
    t = resume_text or ""
    normalized = _normalize(t)

    reasons: List[str] = []

    # Approximate length in pages (assuming ~500–700 words per page)
    words = re.findall(r"\w+", normalized)
    word_count = len(words)
    pages_estimate = word_count / 600.0 if word_count else 0

    score = 1.0

    if pages_estimate < 0.5:
        score *= 0.8
        reasons.append("Resume looks extremely short; ATS may consider it low-signal.")
    elif pages_estimate > 3.0:
        score *= 0.85
        reasons.append("Resume appears very long; ATS and recruiters prefer concise documents.")

    # Look for evidence of multi-column layouts or heavy tables
    if re.search(r"[^\n]{80,}", t):
        # long uninterrupted lines often indicate text extracted from columns
        score *= 0.9
        reasons.append("Resume text extraction suggests complex layout (possible columns).")

    # Check for section headers
    present_headers = [h for h in SECTION_HEADERS if h in normalized]
    if len(present_headers) < 3:
        score *= 0.85
        reasons.append("Standard section headings (Experience, Education, Skills) are sparse or missing.")

    # Very heavy usage of special characters can confuse parsers
    special_chars = re.findall(r"[^a-zA-Z0-9\s\.\,\-\+\/\(\)]", t)
    if len(special_chars) > 50:
        score *= 0.9
        reasons.append("Resume contains many special characters that may confuse parsers.")

    return float(max(0.0, min(1.0, score))), reasons


def _posting_recency_factor(posting_date_str: str) -> Tuple[float, str]:
    """
    Factor that acknowledges older postings may be cold or heavily applied to.
    This doesn't change ATS matching directly, but helps explain priority.
    """
    if not posting_date_str:
        return 1.0, "Posting date not provided; assuming the role is current."

    try:
        dt = parse_date(posting_date_str).date()
    except Exception:
        return 1.0, "Could not parse posting date; ignoring recency factor."

    days_open = (datetime.utcnow().date() - dt).days
    if days_open <= 14:
        return 1.0, "Role looks quite fresh; strong match is more likely to be seen."
    elif days_open <= 45:
        return 0.95, "Role has been open for a few weeks; competition may be higher."
    elif days_open <= 90:
        return 0.9, "Role has been open for a while; may be cold or already in late stages."
    else:
        return 0.85, "Posting appears quite old; response may be unlikely regardless of match."


@dataclass
class ScoreBreakdown:
    overall: float
    keyword_similarity: float
    skills_coverage: float
    seniority_alignment: float
    ats_friendliness: float
    posting_recency_factor: float
    missing_keywords: List[str]
    matched_keywords: List[str]
    seniority_explanation: str
    ats_reasons: List[str]
    recency_explanation: str


def score_resume_against_job(
    jd_text: str,
    resume_text: str,
    posting_date_str: str | None = None,
) -> ScoreBreakdown:
    """
    Main entry point used by the app.
    Returns a ScoreBreakdown with normalized scores in [0, 1] and an overall 0–100 score.
    """
    jd_text = jd_text or ""
    resume_text = resume_text or ""

    keyword_sim = _cosine_similarity(jd_text, resume_text)  # [0,1]
    skills_cov, matched_skills, missing_skills = _skills_coverage(jd_text, resume_text)
    seniority_score, seniority_explanation = _seniority_alignment(jd_text, resume_text)
    ats_score, ats_reasons = _ats_friendliness(resume_text)
    recency_factor, recency_explanation = _posting_recency_factor(posting_date_str or "")

    # Weights roughly reflect how simple ATS search and ranking tends to behave:
    #   - heavy weight on keyword/similarity & explicit skills
    #   - moderate weight on seniority and format
    w_keywords = 0.4
    w_skills = 0.3
    w_seniority = 0.15
    w_ats = 0.15

    base_score = (
        w_keywords * keyword_sim
        + w_skills * skills_cov
        + w_seniority * seniority_score
        + w_ats * ats_score
    )

    overall = base_score * recency_factor
    overall_0_100 = float(round(overall * 100, 1))

    # Select a subset of missing terms to focus on
    missing_top = missing_skills[:25]

    return ScoreBreakdown(
        overall=overall_0_100,
        keyword_similarity=float(round(keyword_sim * 100, 1)),
        skills_coverage=float(round(skills_cov * 100, 1)),
        seniority_alignment=float(round(seniority_score * 100, 1)),
        ats_friendliness=float(round(ats_score * 100, 1)),
        posting_recency_factor=float(round(recency_factor * 100, 1)),
        missing_keywords=missing_top,
        matched_keywords=matched_skills,
        seniority_explanation=seniority_explanation,
        ats_reasons=ats_reasons,
        recency_explanation=recency_explanation,
    )


