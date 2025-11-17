#!/bin/bash

# ATS Match Analyzer - Test Runner Script
# Quick script to run tests with common options

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}ATS Match Analyzer - Test Suite${NC}"
echo "======================================"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Error: Virtual environment not found. Please run setup_and_run.sh first."
    exit 1
fi

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "Installing test dependencies..."
    pip install -q pytest pytest-cov
fi

# Parse command line arguments
case "${1:-all}" in
    all)
        echo -e "\n${GREEN}Running all tests...${NC}"
        python -m pytest -v
        ;;
    coverage)
        echo -e "\n${GREEN}Running tests with coverage...${NC}"
        python -m pytest --cov=. --cov-report=term --cov-report=html
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    quick)
        echo -e "\n${GREEN}Running quick test (no verbose)...${NC}"
        python -m pytest -q
        ;;
    watch)
        echo -e "\n${GREEN}Running tests in watch mode...${NC}"
        python -m pytest -f
        ;;
    app)
        echo -e "\n${GREEN}Running app tests only...${NC}"
        python -m pytest test_app.py -v
        ;;
    scoring)
        echo -e "\n${GREEN}Running scoring tests only...${NC}"
        python -m pytest test_ats_scoring.py -v
        ;;
    optimizer)
        echo -e "\n${GREEN}Running optimizer tests only...${NC}"
        python -m pytest test_resume_optimizer.py -v
        ;;
    *)
        echo "Usage: ./run_tests.sh [all|coverage|quick|watch|app|scoring|optimizer]"
        echo ""
        echo "Options:"
        echo "  all       - Run all tests with verbose output (default)"
        echo "  coverage  - Run tests with coverage report"
        echo "  quick     - Run tests without verbose output"
        echo "  watch     - Run tests in watch mode (re-run on file changes)"
        echo "  app       - Run only app.py tests"
        echo "  scoring   - Run only ats_scoring.py tests"
        echo "  optimizer - Run only resume_optimizer.py tests"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Done!${NC}"
