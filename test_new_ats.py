"""
Quick test to verify the new ATS scoring system works like real ATS platforms.
"""
from backend.app.core.ats_scoring import score_resume_against_job

# Sample job description
job_description = """
Senior Software Engineer - AI/ML Team

We are seeking a Senior Software Engineer with 5+ years of experience to join our AI/ML team.

Required Qualifications:
- 5+ years of professional software development experience
- Strong proficiency in Python and JavaScript
- Experience with React and Node.js
- Bachelor's degree in Computer Science or related field
- Experience with AWS cloud services (S3, EC2, Lambda)
- Docker and Kubernetes experience
- Strong understanding of REST APIs and microservices

Preferred Skills:
- Experience with machine learning frameworks (TensorFlow, PyTorch)
- Knowledge of CI/CD pipelines
- Agile/Scrum methodology experience
- Leadership and mentoring experience

What You'll Do:
- Design and implement scalable backend services
- Work with cross-functional teams
- Mentor junior developers
- Participate in code reviews
"""

# Sample resume
resume = """
John Doe
Senior Software Engineer

SKILLS
Python, JavaScript, TypeScript, React, Node.js, Django, Flask
AWS (EC2, S3, Lambda), Docker, Kubernetes
PostgreSQL, MongoDB, Redis
Git, CI/CD, Jenkins
Machine Learning, TensorFlow, scikit-learn

EXPERIENCE
Senior Software Engineer - Tech Company (2019-Present)
- Lead a team of 5 engineers building scalable microservices
- Implemented REST APIs using Python and Django
- Deployed applications on AWS using Docker and Kubernetes
- Mentored 3 junior developers

Software Engineer - Startup (2017-2019)
- Built React frontend applications
- Developed Node.js backend services
- Worked in Agile/Scrum environment

EDUCATION
Bachelor of Science in Computer Science - University (2017)
"""

# Run scoring
print("Testing new ATS scoring system...")
print("=" * 60)

result = score_resume_against_job(job_description, resume)

print(f"\n✅ Overall Score: {result.overall}/100")
print(f"   Keyword Similarity: {result.keyword_similarity}/100")
print(f"   Skills Coverage: {result.skills_coverage}/100")
print(f"   Seniority Alignment: {result.seniority_alignment}/100")
print(f"   ATS Friendliness: {result.ats_friendliness}/100")

print(f"\n✅ Matched Skills ({len(result.matched_keywords)}):")
for skill in sorted(result.matched_keywords)[:15]:
    print(f"   • {skill}")

print(f"\n❌ Missing Skills ({len(result.missing_keywords)}):")
for skill in sorted(result.missing_keywords)[:10]:
    print(f"   • {skill}")

print("\n" + "=" * 60)
print("Testing with error-prone job description...")
print("=" * 60)

# Test with a problematic JD that previously caused issues
error_jd = """
Error: You need to enable JavaScript to run this app.

AI Agents Platform - Senior Engineer

Help us build the future of AI agents! Our core web platform bundle
integrations for deep learning systems.

What you'll do:
- Build AI agents
- Help team members
- Run app deployment
"""

error_resume = """
Jane Smith
AI/ML Engineer

Skills: Python, TensorFlow, PyTorch, React, JavaScript, Docker, AWS
"""

result2 = score_resume_against_job(error_jd, error_resume)

print(f"\n✅ Overall Score: {result2.overall}/100")
print(f"\n✅ Matched Skills ({len(result2.matched_keywords)}):")
for skill in sorted(result2.matched_keywords):
    print(f"   • {skill}")

print(f"\n❌ Missing Skills ({len(result2.missing_keywords)}):")
for skill in sorted(result2.missing_keywords):
    print(f"   • {skill}")

# Verify we're NOT extracting garbage like "enable", "run app", "agents" anymore
garbage_terms = ["enable", "run", "app", "says", "click", "press", "need to", "you need", "help"]
found_garbage = [skill for skill in result2.matched_keywords + result2.missing_keywords
                 if any(garbage in skill.lower() for garbage in garbage_terms)]

if found_garbage:
    print(f"\n⚠️  WARNING: Found garbage terms: {found_garbage}")
else:
    print(f"\n✅ SUCCESS: No garbage terms found!")
