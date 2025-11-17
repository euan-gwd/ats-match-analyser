# ATS Match Analyser

AI-powered CV optimization tool with React frontend and FastAPI backend.

## Architecture

- **Frontend**: Vite + React + Tailwind CSS
- **Backend**: FastAPI + Python
- **Features**: ATS scoring, keyword analysis, actionable recommendations, GDPR compliance

## Quick Start

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Backend runs on: http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── api/                 # API routes
│   │   └── core/                # Core modules
│   │       ├── ats_scoring.py
│   │       ├── resume_optimizer.py
│   │       ├── security_utils.py
│   │       └── gdpr_compliance.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   ├── components/
│   │   │   ├── ConsentBanner.jsx
│   │   │   ├── UploadForm.jsx
│   │   │   └── Results.jsx
│   │   └── index.css            # Tailwind styles
│   ├── package.json
│   └── tailwind.config.js
│
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
  "matched_keywords": ["python", "react", ...],
  "missing_keywords": ["kubernetes", ...],
  "seniority_explanation": "...",
  "actionable_steps": [...]
}
```

### `GET /api/privacy-notice`
Get GDPR privacy notice

### `POST /api/consent`
Record user consent

## Features

### ✨ CV Analysis
- Keyword matching with TF-IDF
- Skills coverage assessment
- Seniority level alignment
- ATS format compliance

### 🎯 Actionable Recommendations
- Ultra-clear step-by-step instructions
- Before/after examples
- LinkedIn content integration
- Prioritized by impact

### 🔒 Security & GDPR
- Input validation & sanitization
- PII scrubbing from logs
- Rate limiting
- Session management
- No persistent data storage
- GDPR consent tracking

## Development

### Run Tests
```bash
cd backend
pytest
```

### Frontend Dev with Hot Reload
```bash
cd frontend
npm run dev
```

### Backend Dev with Auto-reload
```bash
cd backend
uvicorn app.main:app --reload
```

## Deployment

### Backend
- Use `uvicorn` with Gunicorn for production
- Set CORS origins to your frontend domain
- Enable HTTPS
- Configure rate limiting

### Frontend
```bash
cd frontend
npm run build
```
Serve `dist/` folder with nginx or CDN

## Environment Variables

Create `.env` file in backend/:
```
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
MAX_FILE_SIZE_MB=5
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
```

## License

MIT
