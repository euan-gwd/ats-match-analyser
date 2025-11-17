## ATS Match Analyzer

This app emulates key behaviors of modern Applicant Tracking Systems (ATS) to help you understand **how well your resume matches a specific job** and how likely it is to surface to a recruiter.

You can:
- **Provide a job description** via:
  - Pasting text
  - Uploading a PDF
  - Supplying a job URL
- **Provide the posting date** of the job
- **Upload your resume/CV** as a PDF

The app:
- Parses the job description and your resume
- Applies ATS-like processing (keyword extraction, skills coverage, formatting checks, and relevance scoring)
- Produces:
  - An **overall match score (0–100)** as if you were the recruiter searching in an ATS
  - **Sub-scores** (keyword relevance, skills coverage, seniority alignment, ATS-friendliness)
  - **Concrete recommendations** on how to improve your resume for that specific job

> Note: Real ATS products (Workday, Taleo, Greenhouse, Lever, etc.) each have proprietary algorithms.
> This app approximates widely documented patterns: heavy keyword/skills weighting, field-aware parsing, and basic formatting checks that influence whether a resume is surfaced to recruiters.

---

### 1. Installation

From the project root:

```bash
cd "/ats match analyser"
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

### 2. Running the app

With the virtual environment activated:

```bash
streamlit run app.py
```

Then open the URL that Streamlit prints (usually `http://localhost:8501`) in your browser.

---

### 3. How the scoring works (high level)

The scoring engine currently considers:

- **Keyword & phrase relevance**
  - TF-IDF + cosine similarity between job description and resume
  - Coverage of the most important job-specific keywords and phrases
- **Skills coverage**
  - Matches against a curated list of common technical and business skills
  - Weighs skills mentioned explicitly in the job description more heavily
- **Seniority alignment**
  - Looks at signals like “Senior”, “Lead”, “Manager”, “Junior”, and years of experience
  - Penalizes large mismatches (e.g., junior resume vs. senior role)
- **ATS-friendliness / formatting**
  - Checks for things that commonly break ATS parsing:
    - Overuse of tables/columns (approximated via irregular whitespace patterns)
    - Extremely dense or extremely short resumes
    - Missing standard section headings (Experience, Education, Skills, etc.)
- **Posting date awareness**
  - Uses the posting date to sanity-check experience recency and identify if the role is likely still “hot”

The final score combines these factors into a **0–100 score** with configurable weights, plus human-friendly explanations.

---

### 4. Limitations

- This app does **not** integrate with any proprietary ATS.
- PDF parsing quality depends on how the PDF was generated. Exporting from Word/Google Docs usually works best.
- For highly non-standard resumes (heavy graphics, multi-column designs), any ATS—including this approximation—may mis-parse content.

---

### 5. Future improvements

Potential extensions:

- Use a larger skills ontology (e.g., ESCO / O*NET) to detect more nuanced skills
- Add language detection and multi-language support
- Model-specific emulations (e.g., “score as if this was Workday vs. Lever”)


