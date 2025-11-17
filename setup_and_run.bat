@echo off
REM ATS Match Analyzer - Setup and Run Script (Windows)
REM This script automates the installation and running of the app

echo.
echo 🚀 ATS Match Analyzer - Setup and Run
echo ======================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo ✅ Dependencies installed
echo.
echo 🎯 Starting Streamlit app...
echo    Press Ctrl+C to stop the server
echo.

REM Run the app
streamlit run app.py
