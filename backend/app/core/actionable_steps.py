"""Generate actionable improvement steps from ATS analysis."""
import re
from typing import List, Dict, Set


def _is_meaningful_keyword(keyword: str) -> bool:
    """Filter out noise words and fragments."""
    # Remove single words under 3 chars, common words, fragments
    if len(keyword) < 3:
        return False

    noise_words = {
        'the', 'and', 'for', 'with', 'you', 'this', 'that', 'from', 'have', 'will',
        'are', 'was', 'were', 'been', 'has', 'had', 'can', 'could', 'should', 'would',
        'our', 'your', 'their', 'about', 'into', 'through', 'during', 'before', 'after',
        'need', 'says', 'app', 'run', 'enable', 'says', 'need to', 'you need'
    }

    keyword_lower = keyword.lower().strip()

    # Skip noise words
    if keyword_lower in noise_words:
        return False

    # Skip fragments that look like error messages or UI text
    if any(x in keyword_lower for x in ['you need to', 'click', 'press', 'error', 'warning']):
        return False

    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', keyword):
        return False

    # Skip if it's just numbers or symbols
    if re.match(r'^[\d\s\-\+\.]+$', keyword):
        return False

    return True


def _extract_technical_skills(text: str) -> Set[str]:
    """Extract likely technical skills/tools from text."""
    # Common technical patterns
    patterns = [
        r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin|PHP|Scala)\b',
        r'\b(?:React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|Rails|Laravel)\b',
        r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|CircleCI|Git|Linux|Unix)\b',
        r'\b(?:SQL|NoSQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|DynamoDB)\b',
        r'\b(?:REST|GraphQL|API|CI/CD|DevOps|Agile|Scrum|TDD|Microservices)\b',
        r'\b(?:Machine Learning|ML|AI|Data Science|Analytics|TensorFlow|PyTorch)\b',
        r'\b(?:HTML|CSS|SASS|Webpack|Babel|npm|yarn|TypeScript|ES6)\b',
    ]

    skills = set()
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            skills.add(match.group(0))

    return skills


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

    # Filter missing keywords to only meaningful ones
    meaningful_missing = [kw for kw in breakdown.missing_keywords if _is_meaningful_keyword(kw)]

    # Extract technical skills specifically
    jd_tech_skills = _extract_technical_skills(job_text)
    cv_tech_skills = _extract_technical_skills(resume_text)
    missing_tech_skills = list(jd_tech_skills - cv_tech_skills)[:8]

    # 1. CRITICAL: Missing Technical Skills/Keywords
    if breakdown.skills_coverage < 70 and (missing_tech_skills or meaningful_missing):
        # Prioritize technical skills, then other meaningful keywords
        critical_keywords = missing_tech_skills[:5] + meaningful_missing[:3]
        critical_keywords = critical_keywords[:8]  # Max 8

        if critical_keywords:
            specific_actions = []

            # Group by how to add them
            technical_group = [kw for kw in critical_keywords if kw in missing_tech_skills]
            other_group = [kw for kw in critical_keywords if kw not in missing_tech_skills]

            if technical_group:
                specific_actions.append(
                    "**Technical Skills to Add:**\n"
                )
                for skill in technical_group:
                    specific_actions.append(
                        f'• {skill}\n'
                        f'  → Add to "Skills" or "Technical Skills" section\n'
                        f'  → Mention in at least one bullet under Experience where you used it'
                    )

            if other_group:
                specific_actions.append(
                    "\n**Keywords/Concepts to Include:**\n"
                )
                for keyword in other_group:
                    # Find meaningful context
                    sentences = [s.strip() for s in re.split(r'[.!?]+', job_text) if keyword.lower() in s.lower()]
                    context = sentences[0][:100] + "..." if sentences else ""

                    if context and len(context) > 20:
                        specific_actions.append(
                            f'• "{keyword}"\n'
                            f'  Job context: {context}\n'
                            f'  → Weave this into your experience bullets where relevant'
                        )
                    else:
                        specific_actions.append(
                            f'• "{keyword}"\n'
                            f'  → Add to Skills section and/or mention in experience'
                        )

            steps.append({
                "priority": "🔴 CRITICAL",
                "category": "Missing Required Skills/Keywords",
                "action": f"Add these {len(critical_keywords)} important keywords from the job posting",
                "details": specific_actions,
                "impact": f"Could increase Skills Coverage from {breakdown.skills_coverage:.0f}% to ~{min(90, breakdown.skills_coverage + 25):.0f}%"
            })

    # 2. HIGH PRIORITY: Use Job Description's Exact Language
    if breakdown.keyword_similarity < 70:
        jd_lower = job_text.lower()
        cv_lower = resume_text.lower()

        # Extract requirement phrases (looking for "experience with", "knowledge of", etc.)
        requirement_patterns = [
            r'(?:experience (?:with|in|using|developing)|proficiency (?:in|with)|knowledge of|familiar with|expertise in|skilled (?:in|with)|background in)\s+([^.!?,\n]{10,60})',
            r'(?:must have|should have|required|requirements?:|qualifications?:)\s*([^.!?\n]{15,80})',
            r'(?:responsible for|duties include|you will)\s+([^.!?\n]{15,80})',
        ]

        important_phrases = []
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, job_text, re.IGNORECASE)
            for match in matches:
                phrase = match.group(1).strip()
                # Clean up the phrase
                phrase = re.sub(r'\s+', ' ', phrase)
                if len(phrase) > 15 and phrase.lower() not in cv_lower:
                    important_phrases.append(phrase)

        if important_phrases:
            # Deduplicate similar phrases
            unique_phrases = []
            for phrase in important_phrases[:10]:
                # Check if not too similar to existing
                is_unique = all(phrase.lower() not in existing.lower() and
                              existing.lower() not in phrase.lower()
                              for existing in unique_phrases)
                if is_unique:
                    unique_phrases.append(phrase)

            if unique_phrases[:5]:
                phrase_actions = [
                    "The job description emphasizes these specific requirements:\n"
                ]

                for idx, phrase in enumerate(unique_phrases[:5], 1):
                    phrase_actions.append(
                        f'{idx}. "{phrase}"\n'
                        f'   → Mirror this language in your resume bullets\n'
                        f'   → Use their exact phrasing where you have relevant experience\n'
                    )

                steps.append({
                    "priority": "🟠 HIGH",
                    "category": "Mirror Job Requirements",
                    "action": "Rewrite bullets to match the job's specific language",
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
