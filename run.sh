#!/bin/bash

# ATS Match Analyzer - Quick Run Script
# Runs the app using existing virtual environment

set -e  # Exit on error

echo "🎯 Starting ATS Match Analyzer..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run ./setup_and_run.sh first to set up the environment."
    exit 1
fi

# Activate virtual environment and run
source .venv/bin/activate
python -m streamlit run app.py
