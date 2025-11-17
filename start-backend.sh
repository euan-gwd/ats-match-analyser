#!/bin/bash

echo "🚀 Starting ATS Match Analyser"
echo ""
echo "📋 Prerequisites:"
echo "  - Frontend is already running on http://localhost:5174"
echo "  - Now starting backend..."
echo ""

cd backend
source venv/bin/activate 2>/dev/null || {
    echo "❌ Virtual environment not found. Run setup first:"
    echo "   cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
}

echo "✅ Backend starting on http://localhost:8000"
python -m app.main
