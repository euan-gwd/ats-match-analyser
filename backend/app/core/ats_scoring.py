import re
from dataclasses import dataclass
from datetime import datetime, timezone
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

# Comprehensive skill taxonomy like real ATS systems (Workday, Greenhouse, Lever)
SKILL_TAXONOMY = {
    # Programming Languages
    "programming_languages": {
        "python": ["python", "py", "python3"],
        "javascript": ["javascript", "js", "es6", "es2015", "ecmascript"],
        "typescript": ["typescript", "ts"],
        "java": ["java", "jdk", "jvm"],
        "c++": ["c++", "cpp", "c plus plus"],
        "c#": ["c#", "csharp", "c sharp", ".net"],
        "ruby": ["ruby", "rb"],
        "go": ["golang", "go lang"],
        "rust": ["rust"],
        "swift": ["swift", "swiftui"],
        "kotlin": ["kotlin"],
        "php": ["php"],
        "scala": ["scala"],
        "r": ["r programming", "r language"],
    },

    # Frontend Frameworks
    "frontend": {
        "react": ["react", "react.js", "reactjs", "react native"],
        "angular": ["angular", "angularjs", "angular.js"],
        "vue": ["vue", "vue.js", "vuejs"],
        "svelte": ["svelte", "sveltekit"],
        "nextjs": ["next.js", "nextjs", "next js"],
        "html/css": ["html", "css", "html5", "css3", "sass", "scss", "less"],
        "webpack": ["webpack", "bundler"],
        "vite": ["vite"],
    },

    # Backend Frameworks
    "backend": {
        "node": ["node", "node.js", "nodejs", "express", "express.js"],
        "django": ["django", "django rest framework", "drf"],
        "flask": ["flask"],
        "fastapi": ["fastapi", "fast api"],
        "spring": ["spring", "spring boot", "spring framework"],
        "rails": ["rails", "ruby on rails", "ror"],
        "laravel": ["laravel"],
        "asp.net": ["asp.net", "asp", ".net core"],
    },

    # Databases
    "databases": {
        "sql": ["sql", "structured query language"],
        "postgresql": ["postgresql", "postgres", "psql"],
        "mysql": ["mysql"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis", "redis cache"],
        "elasticsearch": ["elasticsearch", "elastic search", "elk"],
        "dynamodb": ["dynamodb", "dynamo"],
        "cassandra": ["cassandra"],
        "oracle": ["oracle db", "oracle database"],
    },

    # Cloud & DevOps
    "cloud_devops": {
        "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloudformation"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud", "google cloud platform"],
        "docker": ["docker", "containerization"],
        "kubernetes": ["kubernetes", "k8s", "container orchestration"],
        "terraform": ["terraform", "infrastructure as code", "iac"],
        "ansible": ["ansible"],
        "jenkins": ["jenkins"],
        "github actions": ["github actions", "gh actions"],
        "ci/cd": ["ci/cd", "continuous integration", "continuous deployment", "cicd"],
    },

    # Data Science & ML
    "data_ml": {
        "machine learning": ["machine learning", "ml", "deep learning", "neural networks"],
        "tensorflow": ["tensorflow", "tf"],
        "pytorch": ["pytorch", "torch"],
        "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "data analysis": ["data analysis", "data analytics"],
        "data science": ["data science"],
        "ai": ["artificial intelligence", "ai"],
        "nlp": ["nlp", "natural language processing"],
        "computer vision": ["computer vision", "cv", "image processing"],
    },

    # Testing & Quality
    "testing": {
        "unit testing": ["unit test", "unit testing", "tdd", "test driven"],
        "integration testing": ["integration test", "integration testing"],
        "e2e testing": ["e2e", "end to end", "selenium", "cypress", "playwright"],
        "pytest": ["pytest"],
        "jest": ["jest"],
        "mocha": ["mocha"],
    },

    # Methodologies
    "methodologies": {
        "agile": ["agile", "agile methodology", "agile development"],
        "scrum": ["scrum", "scrum master", "sprint"],
        "kanban": ["kanban"],
        "devops": ["devops", "dev ops"],
        "microservices": ["microservices", "microservice architecture"],
        "rest api": ["rest", "rest api", "restful", "rest apis"],
        "graphql": ["graphql", "graph ql"],
    },

    # Soft Skills
    "soft_skills": {
        "leadership": ["leadership", "lead", "leading teams", "team lead"],
        "communication": ["communication", "stakeholder management", "presentation"],
        "collaboration": ["collaboration", "teamwork", "cross-functional"],
        "mentoring": ["mentoring", "coaching", "training"],
        "project management": ["project management", "pm", "program management"],
        "product management": ["product management", "product owner", "roadmap"],
    }
}

# Flatten for quick lookups
ALL_KNOWN_SKILLS = {}
SKILL_SYNONYMS = {}
for category, skills_dict in SKILL_TAXONOMY.items():
    for primary_skill, variants in skills_dict.items():
        ALL_KNOWN_SKILLS[primary_skill] = category
        for variant in variants:
            SKILL_SYNONYMS[variant.lower()] = primary_skill

SENIORITY_KEYWORDS = {
    "intern": ["intern", "internship"],
    "junior": ["junior", "entry level", "entry-level", "graduate", "associate"],
    "mid": ["mid-level", "mid level", "intermediate"],
    "senior": ["senior", "sr.", "sr ", "staff", "principal"],
    "lead": ["lead", "tech lead", "team lead", "engineering lead"],
    "manager": ["manager", "head of", "director", "vp", "chief"],
}


def _normalize(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_keywords(text: str, top_k: int = 30) -> List[str]:
    """
    Extract meaningful skills and keywords using semantic matching against skill taxonomy.
    Works like real ATS platforms (Workday, Greenhouse, Lever) - not just TF-IDF word frequency.
    """
    if not text or len(text.strip()) < 10:
        return []

    text_lower = text.lower()

    # Extract section-specific content (weight Skills section higher)
    skills_section_text = _extract_section_text(text_lower, ["skills", "technical skills"])
    requirements_text = _extract_requirements_text(text_lower)

    matched_skills = set()

    # 1. Match against known skill taxonomy (primary method)
    for variant, primary_skill in SKILL_SYNONYMS.items():
        # Only match if variant is long enough or is a known abbreviation
        if len(variant) < 2:
            continue

        # Check in skills section first (highest priority)
        if variant in skills_section_text and _is_distinct_match(skills_section_text, variant):
            matched_skills.add(primary_skill)
        # Then check requirements sections
        elif variant in requirements_text and _is_distinct_match(requirements_text, variant):
            matched_skills.add(primary_skill)
        # Finally check full text
        elif variant in text_lower and _is_distinct_match(text_lower, variant):
            matched_skills.add(primary_skill)

    # 2. Extract years of experience requirements
    experience_keywords = _extract_experience_keywords(text_lower)
    matched_skills.update(experience_keywords)

    # 3. Extract degree requirements
    degree_keywords = _extract_degree_keywords(text_lower)
    matched_skills.update(degree_keywords)

    # 4. Extract version-specific technologies (Python 3.x, React 18, etc.)
    version_keywords = _extract_versioned_tech(text_lower)
    matched_skills.update(version_keywords)

    return list(matched_skills)[:top_k]


def _extract_section_text(text: str, section_names: List[str]) -> str:
    """
    Extract text from specific sections (Skills, Education, etc.).
    Real ATS systems parse resumes by section and weight them differently.
    """
    section_text = ""
    for section_name in section_names:
        # Find section header
        patterns = [
            f"{section_name}:",
            f"{section_name}\n",
            f"## {section_name}",
            f"**{section_name}**",
        ]

        for pattern in patterns:
            if pattern in text:
                start_idx = text.index(pattern) + len(pattern)
                # Extract until next section or 500 chars
                next_section_idx = len(text)
                for header in SECTION_HEADERS:
                    try:
                        idx = text.index(f"\n{header}", start_idx)
                        next_section_idx = min(next_section_idx, idx)
                    except ValueError:
                        continue

                section_text += text[start_idx:min(start_idx + 500, next_section_idx)]
                break

    return section_text


def _extract_requirements_text(text: str) -> str:
    """
    Extract text from requirement sections (Required:, Qualifications:, etc.).
    Real ATS prioritizes these sections heavily.
    """
    requirement_markers = [
        "required qualifications",
        "required skills",
        "requirements:",
        "qualifications:",
        "what you'll need",
        "must have",
        "you must have",
    ]

    requirements_text = ""
    for marker in requirement_markers:
        if marker in text:
            start_idx = text.index(marker)
            # Extract next 1000 chars
            requirements_text += text[start_idx:start_idx + 1000]

    return requirements_text


def _is_distinct_match(text: str, keyword: str) -> bool:
    """
    Check if keyword appears as a distinct word, not part of another word.
    Example: "python" should match "python development" but not "pythonic"
    """
    # Word boundary pattern
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return bool(re.search(pattern, text))


def _extract_experience_keywords(text: str) -> Set[str]:
    """
    Extract years of experience requirements.
    Example: "5+ years Python" -> "5+ years experience"
    """
    experience_keywords = set()

    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\+?\s*years?\s+(?:in|with|using)\s+\w+',
        r'minimum\s+(\d+)\s+years?',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            experience_keywords.add(f"{match}+ years experience")

    return experience_keywords


def _extract_degree_keywords(text: str) -> Set[str]:
    """
    Extract degree requirements (BS, MS, PhD).
    """
    degree_keywords = set()

    degree_patterns = {
        "bachelor": ["bachelor", "bs", "b.s.", "ba", "b.a.", "undergraduate"],
        "master": ["master", "ms", "m.s.", "ma", "m.a.", "mba", "graduate"],
        "phd": ["phd", "ph.d.", "doctorate", "doctoral"],
    }

    for degree, variants in degree_patterns.items():
        for variant in variants:
            if variant in text:
                degree_keywords.add(f"{degree} degree")
                break

    return degree_keywords


def _extract_versioned_tech(text: str) -> Set[str]:
    """
    Extract version-specific technologies (Python 3.x, React 18, AWS S3, etc.).
    """
    versioned = set()

    # Pattern: technology name followed by version number
    patterns = [
        r'(python|java|node|react|angular|vue)\s+\d+\.?\d*',
        r'(aws|azure|gcp)\s+[a-z0-9]+',  # AWS S3, Azure Blob, etc.
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            versioned.add(match.lower())

    return versioned


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
    """
    Calculate skills coverage using semantic matching against skill taxonomy.
    Real ATS systems match skills semantically, not just by exact text match.
    """
    jd = _normalize(jd_text)
    cv = _normalize(resume_text)
    if not jd or not cv:
        return 0.0, [], []

    # Extract skills from job description using semantic matching
    jd_skills = set(_extract_keywords(jd_text, top_k=50))

    # Extract skills from resume using semantic matching
    cv_skills = set(_extract_keywords(resume_text, top_k=50))

    # Find matched and missing skills
    matched = jd_skills & cv_skills
    missing = jd_skills - cv_skills

    # Calculate coverage score
    if not jd_skills:
        return 0.0, [], []

    coverage_score = len(matched) / len(jd_skills)

    return coverage_score, list(matched), list(missing)


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

    # Level alignment with detailed, actionable feedback
    if diff == 0:
        level_score = 1.0
        explanation_parts.append(f"✓ Your resume's seniority level ({cv_level}) aligns perfectly with the job posting ({jd_level}).")
        explanation_parts.append("This means ATS systems and recruiters will see you as an appropriate match for this role.")
    elif diff == -1:
        level_score = 0.85
        explanation_parts.append(f"⚠️ Your resume appears slightly more junior ({cv_level}) than the role requires ({jd_level}).")
        explanation_parts.append("To strengthen your position:")
        explanation_parts.append("• Emphasize IMPACT and RESULTS in your bullet points (e.g., 'Led team of 5', 'Reduced costs by 30%', 'Architected system serving 1M+ users')")
        explanation_parts.append("• Highlight leadership, mentoring, or ownership experiences")
        explanation_parts.append("• Use action verbs that demonstrate autonomy: 'Architected', 'Drove', 'Owned', 'Spearheaded'")
        explanation_parts.append("• Add metrics and scale to show senior-level contribution")
    elif diff <= -2:
        level_score = 0.6
        explanation_parts.append(f"🚨 Significant mismatch: Your resume reads as {cv_level} level while the job requires {jd_level} level.")
        explanation_parts.append("This is a major red flag for ATS systems and recruiters. You may be automatically screened out.")
        explanation_parts.append("\nTo address this gap:")
        explanation_parts.append("• RE-FRAME your experience: Focus on the most complex, high-impact projects you've worked on")
        explanation_parts.append("• QUANTIFY everything: Show scale, complexity, and business impact with specific numbers")
        explanation_parts.append("• ADD missing experience: Consider freelance projects, open-source contributions, or upskilling to bridge the gap")
        explanation_parts.append("• EMPHASIZE strategic thinking and decision-making in your descriptions")
        explanation_parts.append("• Consider if this role is truly a fit—applying might waste your time and hurt your ATS history")
    elif diff == 1:
        level_score = 0.9
        explanation_parts.append(f"Your resume appears slightly more senior ({cv_level}) than the role ({jd_level}).")
        explanation_parts.append("This can work in your favor, but watch for these risks:")
        explanation_parts.append("• Recruiters may worry you'll leave for a more senior role")
        explanation_parts.append("• They might think you're overqualified and too expensive")
        explanation_parts.append("\nMitigation strategies:")
        explanation_parts.append("• In your cover letter, explicitly state why you're interested in THIS role")
        explanation_parts.append("• Focus resume content on skills DIRECTLY relevant to the job description")
        explanation_parts.append("• Downplay management/leadership aspects if the role is IC-focused")
    else:
        level_score = 0.8
        explanation_parts.append(f"⚠️ Your resume reads as significantly more senior ({cv_level}) than the posted role ({jd_level}).")
        explanation_parts.append("This raises several concerns:")
        explanation_parts.append("• ATS may flag you as overqualified")
        explanation_parts.append("• Hiring managers may assume you'll be bored or leave quickly")
        explanation_parts.append("• Salary expectations may not align")
        explanation_parts.append("\nIf you still want to apply:")
        explanation_parts.append("• Create a targeted resume that focuses on relevant skills, not seniority")
        explanation_parts.append("• Remove or minimize management/leadership responsibilities")
        explanation_parts.append("• Write a cover letter explaining your genuine interest")
        explanation_parts.append("• Consider if this is the right role—applying could hurt your ATS profile")

    # Years of experience consistency check with detailed guidance
    if jd_years and cv_years:
        if cv_years + 1 < jd_years:
            level_score *= 0.8
            years_gap = jd_years - cv_years
            explanation_parts.append(f"\n📅 Experience gap: The job expects {jd_years:.0f}+ years but your resume shows ~{cv_years:.0f} years.")
            explanation_parts.append(f"This {years_gap:.0f}-year gap is significant.")
            explanation_parts.append("\nStrategies to compensate:")
            explanation_parts.append("• COUNT all relevant experience: Include internships, freelance, side projects, open-source")
            explanation_parts.append("• EMPHASIZE accelerated learning and rapid skill acquisition")
            explanation_parts.append("• HIGHLIGHT any mentorship, teaching, or knowledge-sharing that shows maturity")
            explanation_parts.append("• QUANTIFY impact to show you deliver senior-level results despite fewer years")
        elif cv_years >= jd_years:
            explanation_parts.append(f"\n✓ Experience timeline: Your {cv_years:.0f}+ years meets the {jd_years:.0f}+ years requirement.")
            explanation_parts.append("Make sure your resume CLEARLY shows this timeline in your work history section.")

    explanation = "\n".join(explanation_parts) if explanation_parts else "Seniority alignment is unclear—no explicit level keywords detected in the job posting."
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
        dt = parse_date(posting_date_str)
        # If no timezone info, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        return 1.0, "Could not parse posting date; ignoring recency factor."

    # Calculate days since posting (using timezone-aware datetime)
    now = datetime.now(timezone.utc)
    days_open = (now.date() - dt.date()).days

    # Handle future dates or invalid dates
    if days_open < 0:
        return 1.0, "Posting date is in the future; assuming it's current."

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


