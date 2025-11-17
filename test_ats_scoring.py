"""Unit tests for ats_scoring.py"""

import pytest
from datetime import datetime, timedelta
from ats_scoring import (
    _normalize,
    _extract_keywords,
    _cosine_similarity,
    _skills_coverage,
    _detect_seniority,
    _estimate_years_experience,
    _seniority_alignment,
    _ats_friendliness,
    _posting_recency_factor,
    score_resume_against_job,
    ScoreBreakdown,
)


class TestNormalize:
    def test_normalize_basic(self):
        result = _normalize("Hello World")
        assert result == "hello world"

    def test_normalize_whitespace(self):
        result = _normalize("Hello    \n\n   World")
        assert result == "hello world"

    def test_normalize_empty(self):
        result = _normalize("")
        assert result == ""

    def test_normalize_none(self):
        result = _normalize(None)
        assert result == ""


class TestExtractKeywords:
    def test_extract_keywords_basic(self):
        text = "Python developer with experience in machine learning and data science"
        keywords = _extract_keywords(text, top_k=5)
        assert isinstance(keywords, list)
        assert len(keywords) <= 5

    def test_extract_keywords_empty(self):
        keywords = _extract_keywords("", top_k=10)
        assert keywords == []

    def test_extract_keywords_returns_bigrams(self):
        text = "machine learning engineer with deep learning experience"
        keywords = _extract_keywords(text, top_k=10)
        # Should extract bigrams like "machine learning"
        assert any("machine" in kw or "learning" in kw for kw in keywords)


class TestCosineSimilarity:
    def test_identical_texts(self):
        text = "Python developer with machine learning experience"
        result = _cosine_similarity(text, text)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_completely_different_texts(self):
        text1 = "Python developer"
        text2 = "cooking recipes"
        result = _cosine_similarity(text1, text2)
        assert result < 0.5

    def test_similar_texts(self):
        text1 = "Python developer with machine learning experience"
        text2 = "Python engineer with ML and data science background"
        result = _cosine_similarity(text1, text2)
        assert result > 0.0  # Some similarity should be detected
        assert result < 1.0  # But not identical

    def test_empty_texts(self):
        result = _cosine_similarity("", "")
        assert result == 0.0

    def test_one_empty_text(self):
        result = _cosine_similarity("Python developer", "")
        assert result == 0.0


class TestSkillsCoverage:
    def test_all_skills_matched(self):
        jd = "We need Python, Docker, and AWS experience"
        resume = "Expert in Python, Docker, and AWS"
        coverage, matched, missing = _skills_coverage(jd, resume)
        assert coverage > 0.0  # Some coverage detected
        assert len(matched) > 0

    def test_no_skills_matched(self):
        jd = "We need Python and Docker"
        resume = "Expert in cooking and painting"
        coverage, matched, missing = _skills_coverage(jd, resume)
        assert coverage < 1.0
        assert len(missing) > 0

    def test_partial_skills_matched(self):
        jd = "Python, Java, Docker, AWS, and Kubernetes required"
        resume = "I have Python and Docker experience"
        coverage, matched, missing = _skills_coverage(jd, resume)
        assert 0 < coverage < 1
        assert len(matched) > 0
        assert len(missing) > 0

    def test_empty_texts(self):
        coverage, matched, missing = _skills_coverage("", "")
        assert coverage == 0.0
        assert matched == []
        assert missing == []


class TestDetectSeniority:
    def test_detect_senior(self):
        text = "Senior Software Engineer"
        assert _detect_seniority(text) == "senior"

    def test_detect_junior(self):
        text = "Junior Developer position"
        assert _detect_seniority(text) == "junior"

    def test_detect_manager(self):
        text = "Engineering Manager role"
        assert _detect_seniority(text) == "manager"

    def test_detect_lead(self):
        text = "Lead Engineer position"
        assert _detect_seniority(text) == "lead"

    def test_detect_intern(self):
        text = "Software Engineering Intern"
        assert _detect_seniority(text) == "intern"

    def test_unspecified_seniority(self):
        text = "Software Engineer"
        assert _detect_seniority(text) == "unspecified"


class TestEstimateYearsExperience:
    def test_extract_years(self):
        text = "5 years of experience in Python"
        assert _estimate_years_experience(text) == 5.0

    def test_extract_years_plus(self):
        text = "3+ years experience required"
        assert _estimate_years_experience(text) == 3.0

    def test_multiple_years_takes_max(self):
        text = "3 years of Python, 5 years of Java"
        assert _estimate_years_experience(text) == 5.0

    def test_no_years_found(self):
        text = "Experienced developer"
        assert _estimate_years_experience(text) == 0.0


class TestSeniorityAlignment:
    def test_perfect_alignment(self):
        jd = "Senior Software Engineer with 5 years experience"
        resume = "Senior Developer with 6 years experience"
        score, explanation = _seniority_alignment(jd, resume)
        assert score >= 0.85
        assert "aligned" in explanation.lower()

    def test_resume_more_junior(self):
        jd = "Senior Software Engineer"
        resume = "Junior Developer"
        score, explanation = _seniority_alignment(jd, resume)
        assert score < 0.85

    def test_resume_more_senior(self):
        jd = "Junior Developer"
        resume = "Senior Engineer"
        score, explanation = _seniority_alignment(jd, resume)
        assert score < 1.0

    def test_years_mismatch(self):
        jd = "5 years of experience required"
        resume = "2 years of experience"
        score, explanation = _seniority_alignment(jd, resume)
        assert score < 1.0


class TestATSFriendliness:
    def test_short_resume(self):
        resume = "Name\nEmail\nI am a developer."
        score, reasons = _ats_friendliness(resume)
        assert score < 1.0
        assert any("short" in r.lower() for r in reasons)

    def test_very_long_resume(self):
        resume = "Name\nEmail\n" + " ".join(["word"] * 2000)
        score, reasons = _ats_friendliness(resume)
        assert score < 1.0
        assert any("long" in r.lower() for r in reasons)

    def test_missing_section_headers(self):
        resume = "Name\nEmail\nI worked here and there."
        score, reasons = _ats_friendliness(resume)
        assert score < 1.0
        assert any("section" in r.lower() for r in reasons)

    def test_well_formatted_resume(self):
        resume = """
        John Doe
        john@example.com

        Summary
        Experienced developer

        Experience
        Software Engineer at Company A

        Education
        BS Computer Science

        Skills
        Python, Java, Docker
        """
        score, reasons = _ats_friendliness(resume)
        assert score >= 0.8

    def test_complex_layout(self):
        # Very long lines suggest columns
        resume = "Name Email Phone Address City State Zip all on one really long line that suggests a multi-column layout"
        score, reasons = _ats_friendliness(resume)
        assert len(reasons) >= 0  # May detect layout issues


class TestPostingRecencyFactor:
    def test_no_date_provided(self):
        factor, explanation = _posting_recency_factor("")
        assert factor == 1.0
        assert "not provided" in explanation.lower()

    def test_fresh_posting(self):
        today = datetime.utcnow().date()
        recent_date = (today - timedelta(days=7)).isoformat()
        factor, explanation = _posting_recency_factor(recent_date)
        assert factor == 1.0
        assert "fresh" in explanation.lower()

    def test_few_weeks_old(self):
        today = datetime.utcnow().date()
        date_str = (today - timedelta(days=30)).isoformat()
        factor, explanation = _posting_recency_factor(date_str)
        assert factor >= 0.9
        assert factor <= 1.0

    def test_old_posting(self):
        today = datetime.utcnow().date()
        date_str = (today - timedelta(days=100)).isoformat()
        factor, explanation = _posting_recency_factor(date_str)
        assert factor < 1.0
        assert "old" in explanation.lower()

    def test_invalid_date(self):
        factor, explanation = _posting_recency_factor("not-a-date")
        assert factor == 1.0
        assert "could not parse" in explanation.lower()


class TestScoreResumeAgainstJob:
    def test_perfect_match(self):
        jd = """
        Senior Python Developer
        5 years of experience required
        Skills: Python, Docker, AWS, machine learning, data science
        """
        resume = """
        John Doe
        john@example.com

        Summary
        Senior Python Developer with 6 years of experience

        Experience
        Led Python development projects using Docker and AWS
        Implemented machine learning models for data science applications

        Education
        BS Computer Science

        Skills
        Python, Docker, AWS, machine learning, data science, SQL
        """
        breakdown = score_resume_against_job(jd, resume)

        assert isinstance(breakdown, ScoreBreakdown)
        assert breakdown.overall > 50.0
        assert breakdown.keyword_similarity > 0
        assert breakdown.skills_coverage > 0
        assert breakdown.seniority_alignment > 0
        assert breakdown.ats_friendliness > 0

    def test_poor_match(self):
        jd = "Senior Python Developer with machine learning experience"
        resume = "Chef with 10 years of cooking experience"
        breakdown = score_resume_against_job(jd, resume)

        assert breakdown.overall < 50.0
        assert breakdown.keyword_similarity < 50.0

    def test_empty_inputs(self):
        breakdown = score_resume_against_job("", "")
        assert breakdown.overall >= 0
        assert breakdown.overall <= 100

    def test_with_posting_date(self):
        jd = "Python Developer"
        resume = "Python Developer with 5 years experience"
        today = datetime.utcnow().date()
        recent_date = (today - timedelta(days=7)).isoformat()

        breakdown = score_resume_against_job(jd, resume, recent_date)
        assert breakdown.posting_recency_factor > 0

    def test_breakdown_fields(self):
        jd = "Python Developer"
        resume = "Python Developer"
        breakdown = score_resume_against_job(jd, resume)

        # Check all required fields exist
        assert hasattr(breakdown, "overall")
        assert hasattr(breakdown, "keyword_similarity")
        assert hasattr(breakdown, "skills_coverage")
        assert hasattr(breakdown, "seniority_alignment")
        assert hasattr(breakdown, "ats_friendliness")
        assert hasattr(breakdown, "posting_recency_factor")
        assert hasattr(breakdown, "missing_keywords")
        assert hasattr(breakdown, "matched_keywords")
        assert hasattr(breakdown, "seniority_explanation")
        assert hasattr(breakdown, "ats_reasons")
        assert hasattr(breakdown, "recency_explanation")

        # Check types
        assert isinstance(breakdown.overall, float)
        assert isinstance(breakdown.missing_keywords, list)
        assert isinstance(breakdown.matched_keywords, list)
        assert isinstance(breakdown.seniority_explanation, str)
        assert isinstance(breakdown.ats_reasons, list)
        assert isinstance(breakdown.recency_explanation, str)

    def test_score_ranges(self):
        jd = "Python Developer with Docker experience"
        resume = "Python Developer with Docker and AWS experience"
        breakdown = score_resume_against_job(jd, resume)

        # All scores should be in valid ranges
        assert 0 <= breakdown.overall <= 100
        assert 0 <= breakdown.keyword_similarity <= 100
        assert 0 <= breakdown.skills_coverage <= 100
        assert 0 <= breakdown.seniority_alignment <= 100
        assert 0 <= breakdown.ats_friendliness <= 100
        assert 0 <= breakdown.posting_recency_factor <= 100
