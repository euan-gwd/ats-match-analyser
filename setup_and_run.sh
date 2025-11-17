#!/bin/bash

# ATS Match Analyzer - Setup and Run Script
# This script automates the installation and running of the app

set -e  # Exit on error

echo "🚀 ATS Match Analyzer - Setup and Run"
echo "======================================"
echo ""

# Check if virtual environment exists and has pip
if [ ! -d ".venv" ] || [ ! -f ".venv/bin/pip" ]; then
    if [ -d ".venv" ]; then
        echo "🗑️  Removing incomplete virtual environment..."
        rm -rf .venv
    fi
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv --copies
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Verify we're using the venv's Python
VENV_PYTHON=".venv/bin/python"

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
$VENV_PYTHON -m pip install --upgrade pip --quiet
$VENV_PYTHON -m pip install -r requirements.txt --quiet

echo "✅ Dependencies installed"
echo ""
echo "🎯 Starting Streamlit app..."
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the app
$VENV_PYTHON -m streamlit run app.py
