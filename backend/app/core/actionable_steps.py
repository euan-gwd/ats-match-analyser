"""Generate actionable improvement steps from ATS analysis."""
import re
from typing import List, Dict


def generate_actionable_steps(breakdown, job_text: str, resume_text: str, linkedin_text: str = "") -> List[Dict]:
    """
    Generate specific, actionable recommendations based on ATS scoring breakdown.

    Args:
        breakdown: ScoreBreakdown object with analysis results
        job_text: Job description text
        resume_text: Resume/CV text
        linkedin_text: Optional LinkedIn profile text

    Returns:
        List of actionable steps with priority, category, action, details, and impact
    """
    steps = []

    # 1. CRITICAL: Missing Required Keywords
    if breakdown.skills_coverage < 70 and breakdown.missing_keywords:
        missing_critical = breakdown.missing_keywords[:8]
        specific_actions = []

        for keyword in missing_critical:
            # Try to find context in job description
            sentences = re.split(r'[.!?]+', job_text)
            context = ""
            for sent in sentences:
                if keyword.lower() in sent.lower():
                    context = sent.strip()[:120]
                    break

            if context:
                specific_actions.append(
                    f'• "{keyword}" - Job says: "{context}..."\n'
                    f'  → Add to Skills section AND mention in a relevant bullet point'
                )
            else:
                specific_actions.append(
                    f'• "{keyword}"\n'
                    f'  → Add to Skills section and describe where/how you used it'
                )

        steps.append({
            "priority": "🔴 CRITICAL",
            "category": "Missing Required Keywords",
            "action": f"Add these {len(missing_critical)} critical keywords from the job description",
            "details": specific_actions,
            "impact": f"Could increase Skills Coverage from {breakdown.skills_coverage:.0f}% to ~{min(90, breakdown.skills_coverage + 25):.0f}%"
        })

    # 2. HIGH PRIORITY: Keyword Match Improvement
    if breakdown.keyword_similarity < 70:
        # Extract key phrases from job description
        jd_lower = job_text.lower()
        cv_lower = resume_text.lower()

        # Find important phrases (2-3 words) that appear multiple times in JD
        phrases = re.findall(r'\b(?:\w+\s+){1,2}\w+\b', jd_lower)
        phrase_counts = {}
        for phrase in phrases:
            phrase = phrase.strip()
            if len(phrase) > 10 and phrase not in phrase_counts:
                phrase_counts[phrase] = jd_lower.count(phrase)

        # Get top phrases not in resume
        important_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        missing_phrases = [p for p, count in important_phrases if count >= 2 and p not in cv_lower][:5]

        if missing_phrases:
            phrase_actions = [
                "Replace generic descriptions with these exact phrases from the job posting:\n"
            ]

            for phrase in missing_phrases:
                phrase_actions.append(
                    f'• "{phrase}"\n'
                    f'  → Use this EXACT wording in 2-3 different bullet points'
                )

            steps.append({
                "priority": "🟠 HIGH",
                "category": "Mirror Job Description Language",
                "action": "Use the employer's exact terminology and phrases",
                "details": phrase_actions,
                "impact": f"Could increase Keyword Match from {breakdown.keyword_similarity:.0f}% to ~{min(90, breakdown.keyword_similarity + 20):.0f}%"
            })

    # 3. HIGH PRIORITY: LinkedIn Profile Content
    if linkedin_text and len(linkedin_text) > 100:
        linkedin_lower = linkedin_text.lower()
        cv_lower = resume_text.lower()

        # Find missing keywords that exist in LinkedIn
        linkedin_has = []
        for keyword in breakdown.missing_keywords[:10]:
            if keyword.lower() in linkedin_lower and keyword.lower() not in cv_lower:
                # Find context
                match = re.search(rf'([^.!?\n]{{0,80}}{re.escape(keyword)}[^.!?\n]{{0,80}})[.!?\n]',
                                linkedin_text, re.IGNORECASE)
                if match:
                    linkedin_has.append({
                        'keyword': keyword,
                        'context': match.group(1).strip()
                    })

        if linkedin_has:
            linkedin_actions = [
                "🔗 QUICK WIN: Copy these from your LinkedIn profile:\n"
            ]

            for idx, item in enumerate(linkedin_has[:5], 1):
                linkedin_actions.append(
                    f'{idx}. Find: "{item["context"][:80]}..."\n'
                    f'   Copy → Paste into your CV Experience or Skills section\n'
                )

            steps.append({
                "priority": "🟠 HIGH",
                "category": "LinkedIn Profile Content",
                "action": "Copy-paste content from your LinkedIn (5-minute task)",
                "details": linkedin_actions,
                "impact": f"Instant addition of {len(linkedin_has)} required keywords"
            })

    # 4. MEDIUM: ATS Formatting Issues
    if breakdown.ats_friendliness < 80 and breakdown.ats_reasons:
        format_actions = []

        for reason in breakdown.ats_reasons:
            if "short" in reason.lower():
                format_actions.append(
                    "• Your resume appears too short\n"
                    "  → Expand with more detail: add metrics, context, and achievements to each role"
                )
            elif "long" in reason.lower():
                format_actions.append(
                    "• Your resume is too long\n"
                    "  → Cut to 2 pages max: remove older/irrelevant roles, condense bullets"
                )
            elif "column" in reason.lower() or "layout" in reason.lower():
                format_actions.append(
                    "• Complex layout detected (columns/tables)\n"
                    "  → Switch to single-column format: ATS systems struggle with multi-column layouts"
                )
            elif "header" in reason.lower():
                format_actions.append(
                    "• Missing standard section headers\n"
                    "  → Add clear headers: Experience, Education, Skills (use standard names)"
                )
            elif "special" in reason.lower():
                format_actions.append(
                    "• Too many special characters\n"
                    "  → Simplify formatting: use standard bullets, avoid icons/graphics"
                )

        if format_actions:
            steps.append({
                "priority": "🟡 MEDIUM",
                "category": "ATS Format Optimization",
                "action": "Fix formatting issues that confuse applicant tracking systems",
                "details": format_actions,
                "impact": f"Could increase ATS Friendliness from {breakdown.ats_friendliness:.0f}% to ~{min(95, breakdown.ats_friendliness + 15):.0f}%"
            })

    # 5. MEDIUM: Add Quantifiable Achievements
    cv_lower = resume_text.lower()
    has_metrics = bool(re.search(r'\d+%|\$\d+|\d+\+?\s+(?:users|people|employees|projects|customers)', cv_lower))

    if not has_metrics or breakdown.keyword_similarity < 75:
        metric_actions = [
            "Add numbers and metrics to demonstrate impact:\n",
            "• Replace: 'Improved system performance'\n"
            "  With: 'Improved system performance by 40%, reducing load time from 3s to 1.8s'\n",
            "• Replace: 'Managed a team'\n"
            "  With: 'Led team of 5 engineers, delivering 12 features across 4 sprints'\n",
            "• Replace: 'Built a dashboard'\n"
            "  With: 'Built analytics dashboard serving 500+ daily users, increasing engagement 35%'\n",
            "\nEvery bullet point should answer: HOW MUCH? HOW MANY? BY HOW MUCH?"
        ]

        steps.append({
            "priority": "🟡 MEDIUM",
            "category": "Quantify Your Impact",
            "action": "Add specific numbers and metrics to your achievements",
            "details": metric_actions,
            "impact": "Numbers make your resume stand out and prove real impact"
        })

    # 6. MEDIUM: Professional Summary
    has_summary = bool(re.search(r'(?:summary|objective|profile|about me):', cv_lower))

    if not has_summary or breakdown.keyword_similarity < 70:
        # Extract role title from job
        role_match = re.search(r'(?:job title|position|role):\s*([^\n]{10,60})', job_text, re.IGNORECASE)
        if not role_match:
            # Try to get from first line or strong patterns
            role_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})', job_text)

        role_title = role_match.group(1).strip() if role_match else "Software Engineer"

        # Get top 3 matched keywords
        top_skills = breakdown.matched_keywords[:3] if breakdown.matched_keywords else ["relevant skill", "key technology", "domain expertise"]

        summary_actions = [
            "Add a 2-3 line summary at the top of your resume:\n",
            f'Example:\n'
            f'"{role_title} with [X]+ years building [type of systems]. '
            f'Expert in {", ".join(top_skills[:2])}, and {top_skills[2] if len(top_skills) > 2 else "relevant technology"}. '
            f'Proven track record of [key achievement from job description]."\n',
            "\nThis summary:\n"
            "• Mirrors the job title exactly\n"
            "• Front-loads your top matching keywords\n"
            "• Appears in ATS search results preview"
        ]

        steps.append({
            "priority": "🟡 MEDIUM",
            "category": "Professional Summary",
            "action": "Add keyword-rich summary at the top (if missing or generic)",
            "details": summary_actions,
            "impact": "Helps ATS and recruiters immediately see you're a match"
        })

    # If no steps were generated, add a general recommendation
    if not steps:
        steps.append({
            "priority": "🟢 GOOD",
            "category": "General Optimization",
            "action": "Your resume is already well-optimized for this role",
            "details": [
                "Your ATS score is solid! A few final polish items:\n",
                "• Double-check that every bullet starts with a strong action verb\n",
                "• Ensure your most relevant experience is in the top half of page 1\n",
                "• Proofread for any typos (ATS is sensitive to spelling)\n",
                "• Save as a .PDF with a clear filename: FirstName_LastName_Resume.pdf"
            ],
            "impact": "Small refinements can push you from 'good' to 'great'"
        })

    return steps
