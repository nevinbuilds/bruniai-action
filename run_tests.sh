#!/bin/bash
set -e

# Activate virtual environment if it exists
if [ -d "venv310" ]; then
    echo "Activating virtual environment..."
    source venv310/bin/activate
fi

# Install dependencies if needed
if [ "$1" == "--install" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the tests
echo "Running tests..."
pytest

# Generate coverage report
echo "Generating coverage report..."
pytest --cov=scripts --cov-report=html

echo "Tests completed! Coverage report is available in htmlcov/ directory."
