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

### 1. Quick Start (Automated)

The easiest way to install and run the app:

**macOS/Linux:**
```bash
./setup_and_run.sh
```

**Windows:**
```cmd
setup_and_run.bat
```

This script will:
- Create a virtual environment (if it doesn't exist)
- Install all dependencies
- Launch the Streamlit app

Then open the URL that Streamlit prints (usually `http://localhost:8501`) in your browser.

---

### 2. Manual Installation (Alternative)

If you prefer manual setup, from the project root:

```bash
cd "/ats match analyser"
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then run:

```bash
streamlit run app.py
```

---

### 3. Running Tests

This project includes comprehensive unit tests to ensure reliability.

**Run all tests:**
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pytest
```

**Run tests with coverage report:**
```bash
pytest --cov=. --cov-report=term --cov-report=html
```

**View HTML coverage report:**
```bash
open htmlcov/index.html  # On macOS
# Or navigate to htmlcov/index.html in your browser
```

**Test Coverage:** 85%+ (core business logic covered)

For more details on testing, see [TESTING.md](TESTING.md).

---

### 4. How the scoring works (high level)

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

### 5. Limitations

- This app does **not** integrate with any proprietary ATS.
- PDF parsing quality depends on how the PDF was generated. Exporting from Word/Google Docs usually works best.
- For highly non-standard resumes (heavy graphics, multi-column designs), any ATS—including this approximation—may mis-parse content.

---

### 6. Future improvements

Potential extensions:

- Use a larger skills ontology (e.g., ESCO / O*NET) to detect more nuanced skills
- Add language detection and multi-language support
- Model-specific emulations (e.g., “score as if this was Workday vs. Lever”)


