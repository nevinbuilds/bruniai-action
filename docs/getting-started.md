# Getting Started

This guide will help you set up and start using the Visual Regression Testing tool locally using Python.

## Prerequisites

- Python 3.10 or higher
- Node.js and npm
- Git
- OpenAI API key

## Installation Steps

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Set Up Python Virtual Environment**

   ```bash
   python3.10 -m venv venv310
   source venv310/bin/activate  # On Windows, use: venv310\Scripts\activate
   ```

3. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install the Package in Development Mode**

   ```bash
   pip install -e .
   ```

5. **Install Playwright MCP**

   ```bash
   npm install -g @playwright/mcp
   ```

6. **Install Playwright Browsers**

   ```bash
   npx playwright install
   ```

7. **Set Up Environment Variables**
   Create a `.env` file in the root directory and add your OpenAI API key:

   ```
   OPENAI_API_KEY=your_api_key_here
   ```

   **Optional (for advanced features):**

   - `GITHUB_TOKEN` – for posting PR comments
   - `BRUNI_TOKEN` and `BRUNI_API_URL` – for Bruni API integration

## Running the Visual Tests

1. **Start the MCP Server**

   ```bash
   npx @playwright/mcp@latest --port 8931
   ```

2. **Run the Visual Regression Tests**

   You can run the tests with either of the following commands:

   ```bash
   python -m src.runner.__main__ --base-url <production-url> --pr-url <pull-request-url>
   # or
   python src/runner/__main__.py --base-url <production-url> --pr-url <pull-request-url>
   ```

   Example:

   ```bash
   python -m src.runner.__main__ --base-url https://www.brunivisual.com/ --pr-url https://bruni-website-git-changefoo-nevinbuilds.vercel.app/
   ```

## Understanding the Output

The tool will:

1. Capture screenshots of both the production and PR versions
2. Compare the images and highlight differences
3. Generate a report with the findings
4. Provide AI-powered analysis of the changes

## Next Steps

- Review the [Configuration Guide](configuration.md) to customize the testing behavior
- Check out [Usage Examples](usage-examples.md) for more advanced scenarios
- Learn about the [Architecture](architecture.md) to understand how the tool works
