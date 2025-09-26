#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting setup for Visual Regression Testing tool..."

echo "1. Cloning the repository (skipped if already cloned)"
# Assuming the repository is already cloned since the script is run from within it.

echo "2. Setting up Python Virtual Environment..."
python3.10 -m venv venv310
source venv310/bin/activate

echo "3. Installing Python Dependencies..."
pip install -r requirements.txt

echo "4. Installing the Package in Development Mode..."
pip install -e .

echo "5. Installing Playwright MCP..."
npm install -g @playwright/mcp

echo "6. Installing Playwright Browsers..."
npx playwright install

echo "7. Setting up Environment Variables (you will need to create .env manually if it doesn't exist)..."
# The .env file needs to be created manually by the user, this script won't create it with sensitive info.
echo "Please create a .env file in the root directory with OPENAI_API_KEY=your_api_key_here"
echo "Optional: GITHUB_TOKEN, BRUNI_TOKEN, BRUNI_API_URL"

echo "8. Starting Playwright MCP server in the background..."
npx @playwright/mcp@latest --port 8931 & # Run in background

echo "Setup complete. To run the tests, start the MCP server and then run the tests as described in docs/getting-started.md"
