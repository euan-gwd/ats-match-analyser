# ATS Match Analyser

AI-powered CV optimization tool that analyzes resumes against job descriptions using **enterprise-grade ATS matching** technology.

## 🎯 Key Features

- **Enterprise-Grade ATS Scoring**: Uses semantic matching like real ATS platforms (Workday, Greenhouse, Lever)
- **500+ Skill Taxonomy**: Comprehensive skill database across programming, frameworks, cloud, methodologies
- **Intelligent Extraction**: Recognizes experience years, degree requirements, and version-specific technologies
- **Section-Aware Parsing**: Prioritizes Skills and Requirements sections like real ATS systems
- **Actionable Recommendations**: Step-by-step guidance to improve resume match
- **GDPR Compliant**: Full privacy controls with no persistent data storage

## Architecture

- **Frontend**: Vite 7.2 + React 19 + Tailwind CSS v4
- **Backend**: FastAPI + Python 3.14
- **ATS Engine**: Semantic skill matching with 500+ skills across 9 categories
- **Security**: Rate limiting, PII scrubbing, input validation, session management

## 🚀 Quick Start

### One-Command Setup

```bash
./start.sh
```

This script will:
1. Set up Python virtual environment
2. Install all dependencies
3. Start backend server (http://localhost:8000)
4. Start frontend dev server (http://localhost:5173)

### Manual Setup

#### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application
│   │   ├── api/                        # API routes
│   │   └── core/                       # Core modules
│   │       ├── ats_scoring.py          # Enterprise-grade ATS matching engine
│   │       ├── actionable_steps.py     # Recommendation generator
│   │       ├── security_utils.py       # Security & validation
│   │       └── gdpr_compliance.py      # Privacy controls
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     # Main app component
│   │   ├── components/
│   │   │   ├── ConsentBanner.jsx       # GDPR consent
│   │   │   ├── UploadForm.jsx          # File upload & JD input
│   │   │   └── Results.jsx             # Score visualization
│   │   └── index.css                   # Tailwind v4 styles
│   ├── vite.config.js                  # Vite + Tailwind plugin
│   ├── package.json
│   └── tailwind.config.js
│
├── start.sh                             # One-command startup script
├── ATS_IMPROVEMENTS.md                  # Technical documentation
└── README.md
```

## API Endpoints

### `POST /api/analyze`
Analyze CV against job description
- **Body**: `multipart/form-data`
  - `cv_file`: PDF file
  - `job_description`: Text (optional if job_url provided)
  - `job_url`: URL (optional if job_description provided)
  - `linkedin_url`: URL (optional)
  - `session_id`: String

**Response**:
```json
{
  "overall": 75.5,
  "keyword_similarity": 68.0,
  "skills_coverage": 82.0,
  "seniority_alignment": 90.0,
  "ats_friendliness": 75.0,
  "posting_recency_factor": 100.0,
  "matched_keywords": [
    "python",
    "javascript",
    "react",
    "docker",
    "aws",
    "bachelor degree",
    "5+ years experience"
  ],
  "missing_keywords": [
    "kubernetes",
    "typescript",
    "ci/cd"
  ],
  "seniority_explanation": "Your profile shows strong senior-level indicators...",
  "ats_reasons": [
    "Clear section headers detected",
    "Good use of bullet points"
  ],
  "actionable_steps": [
    {
      "priority": "high",
      "category": "Missing Skills",
      "action": "Add Kubernetes to your skills",
      "details": ["Add to Skills section", "Mention in project descriptions"],
      "impact": "Critical skill gap for this role"
    }
  ]
}
```

### `GET /api/privacy-notice`
Get GDPR privacy notice

### `POST /api/consent`
Record user consent

## Features

### ✨ Enterprise-Grade ATS Scoring

**How it works like real ATS platforms:**

1. **Comprehensive Skill Taxonomy** (500+ skills)
   - Programming Languages: Python, JavaScript, Java, Go, Rust, Swift, etc.
   - Frontend/Backend: React, Vue, Angular, Django, FastAPI, Spring, etc.
   - Cloud & DevOps: AWS, Azure, GCP, Docker, Kubernetes, Terraform
   - Data Science & ML: TensorFlow, PyTorch, pandas, scikit-learn
   - Databases: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch
   - Methodologies: Agile, Scrum, DevOps, microservices, REST API
   - Soft Skills: Leadership, communication, mentoring, collaboration

2. **Semantic Matching with Synonyms**
   - `javascript` → ["javascript", "js", "es6", "es2015", "ecmascript"]
   - `kubernetes` → ["kubernetes", "k8s", "container orchestration"]
   - `machine learning` → ["ml", "deep learning", "neural networks"]

3. **Section-Aware Parsing**
   - Skills section weighted highest
   - Requirements sections (Required:, Must Have:) prioritized
   - Word boundary validation prevents false matches

4. **Structured Data Extraction**
   - Experience: "5+ years of experience", "minimum 3 years Python"
   - Degrees: Bachelor's, Master's, PhD with variant recognition (BS, B.S., MS, Ph.D.)
   - Versioned tech: Python 3.x, React 18, AWS S3

### 🎯 Intelligent Analysis

- **Keyword Similarity**: TF-IDF cosine similarity for overall text matching
- **Skills Coverage**: Semantic matching of required vs. present skills
- **Seniority Alignment**: Detailed multi-paragraph career guidance
- **ATS Friendliness**: Format and structure recommendations
- **Posting Recency**: Time-based scoring adjustment

### 📋 Actionable Recommendations

Six types of prioritized recommendations:
1. **Missing Skills**: Specific technical gaps to address
2. **Mirror Language**: Match job description terminology
3. **LinkedIn Content**: Profile optimization suggestions
4. **ATS Format**: Structural improvements for parsing
5. **Quantify Impact**: Add metrics and achievements
6. **Summary**: Executive summary enhancement

### 🔒 Security & Privacy

- **No Persistent Storage**: All data processed in-memory
- **PII Scrubbing**: Removes sensitive info from logs
- **Rate Limiting**: 10 requests per 60 seconds per session
- **Input Validation**: File size limits (5MB), content safety checks
- **Session Management**: 30-minute timeout
- **GDPR Compliance**: Explicit consent tracking, privacy notice, data export

## Development

### Run Tests
```bash
cd backend
source venv/bin/activate
pytest

# Or test the scoring engine directly
python test_new_ats.py
```

### Code Coverage
```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Frontend Dev with Hot Reload
```bash
cd frontend
npm run dev
```

### Backend Dev with Auto-reload
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

## How the ATS Scoring Works

### Traditional ATS (Before)
❌ Used TF-IDF to extract "important" words
❌ Resulted in garbage: "enable", "run", "agents", "help", "says"
❌ No semantic understanding of skills

### Our Enterprise-Grade System (After)
✅ **Skill Taxonomy Matching**: 500+ predefined skills with synonyms
✅ **Section-Aware**: Prioritizes Skills and Requirements sections
✅ **Semantic Extraction**: Recognizes experience, degrees, versions
✅ **Word Boundary Validation**: Prevents false matches
✅ **Real Results**: Extracts actual skills like "python", "react", "docker", "5+ years experience"

**Example:**
- Job Description: "5+ years Python, React, AWS required. Bachelor's degree."
- Resume: "6 years experience. Python, React, Docker, AWS. BS Computer Science."
- **Matched**: python, react, aws, bachelor degree, 5+ years experience
- **Missing**: (none - 100% match!)

See `ATS_IMPROVEMENTS.md` for detailed technical documentation.

## Deployment

### Backend Production

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Production checklist:**
- ✅ Set CORS origins to your frontend domain
- ✅ Enable HTTPS/TLS
- ✅ Configure environment variables
- ✅ Set up monitoring and logging
- ✅ Configure rate limiting per your needs
- ✅ Review security settings in `security_utils.py`

### Frontend Production

```bash
cd frontend
npm run build
```

Serve `dist/` folder with:
- Nginx
- Apache
- Vercel / Netlify / Cloudflare Pages
- AWS S3 + CloudFront
- Any static hosting service

## Environment Variables

Create `.env` file in `backend/` directory:

```env
# Environment
ENVIRONMENT=production

# Security
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
MAX_FILE_SIZE_MB=5
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Session
SESSION_TIMEOUT_MINUTES=30

# Optional: API Keys for job scraping
LINKEDIN_API_KEY=your_key_here
```

## Technology Stack

### Frontend
- **Vite 7.2.2**: Lightning-fast build tool
- **React 19.2.0**: Modern UI library with concurrent features
- **Tailwind CSS v4.1.17**: Utility-first CSS with new Vite plugin
- **@tailwindcss/vite**: Official Vite integration for Tailwind v4
- **PostCSS**: CSS transformation pipeline

### Backend
- **FastAPI**: High-performance async web framework
- **Python 3.14**: Latest Python with performance improvements
- **pypdf**: PDF text extraction
- **scikit-learn**: TF-IDF vectorization and cosine similarity
- **BeautifulSoup4**: HTML parsing for job URLs
- **python-dateutil**: Date parsing and validation
- **uvicorn**: ASGI server for FastAPI

### ATS Engine
- **500+ Skill Taxonomy**: Comprehensive skill database
- **Semantic Matching**: Synonym recognition and word boundary validation
- **Section-Aware Parsing**: Prioritizes Skills and Requirements sections
- **Structured Extraction**: Experience years, degrees, versioned tech

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest` (backend), `npm test` (frontend)
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Troubleshooting

### Backend won't start
```bash
# Check Python version (need 3.10+)
python3 --version

# Reinstall dependencies
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend build fails
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### ATS scoring returns empty results
- Check that job description and resume both have content
- Verify PDF is text-based (not scanned image)
- Check backend logs for errors: `tail -f backend/logs/app.log`

## Documentation

- `README.md` - This file (getting started, features, deployment)
- `ATS_IMPROVEMENTS.md` - Technical deep-dive on ATS scoring improvements
- `SECURITY_README.md` - Security features and best practices
- `TESTING.md` - Test coverage and testing guide

## License

MIT

---

**Built with ❤️ for job seekers everywhere**
