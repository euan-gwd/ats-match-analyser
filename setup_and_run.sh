#!/bin/bash

# ATS Match Analyzer - Setup and Run Script
# This script automates the installation and running of the app

set -e  # Exit on error

echo "🚀 ATS Match Analyzer - Setup and Run"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "✅ Dependencies installed"
echo ""
echo "🎯 Starting Streamlit app..."
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the app
streamlit run app.py
