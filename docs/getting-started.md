# Getting Started

This guide will help you set up and start using the Visual Regression Testing tool locally using Python.

## Prerequisites

- Python 3.10 or higher
- Node.js and npm
- Git
- OpenAI API key

## Installation Steps

We highly recommend using the automated setup script for a smoother experience.

1.  **Run the Setup Script (Recommended)**

    ```bash
    ./scripts/setup.sh
    ```

    This script will perform all the necessary installation steps, from setting up the Python virtual environment to installing Playwright browsers.

    After running the script, please proceed to step 8 (Set Up Environment Variables) if you haven't already.

2.  **Clone the Repository**

    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

3.  **Set Up Python Virtual Environment**

    ```bash
    python3 -m venv venv310
    source venv310/bin/activate  # On Windows, use: venv310\Scripts\activate
    # IMPORTANT: Ensure your virtual environment is activated before proceeding with the following steps.
    ```

4.  **Install Python Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Install the Package in Development Mode**

    ```bash
    pip install -e .
    ```

6.  **Install Playwright MCP**

    ```bash
    npm install -g @playwright/mcp
    ```

7.  **Install Playwright Browsers**

    ```bash
    npx playwright install
    ```

8.  **Set Up Environment Variables**
    Create a `.env` file in the root directory and add your OpenAI API key:

    ```
    OPENAI_API_KEY=your_api_key_here
    ```

    **Optional (for advanced features):**

    - `GITHUB_TOKEN` – for posting PR comments
    - `BRUNI_TOKEN` and `BRUNI_API_URL` – for Bruni API integration

## Running the Visual Tests

1. **Start the MCP Server**

   If you ran the `setup.sh` script, the MCP server should already be running in the background. If you need to start it manually or in a separate terminal tab, use the following command:

   ```bash
   npx @playwright/mcp@latest --port 8931
   ```

2. **Run the Visual Regression Tests**

   You can run the tests with either of the following commands:

   ```bash
   GITHUB_TOKEN=<github-token> python src/runner/__main__.py --base-url <production-url> --pr-url <pull-request-url> --pages '<pages>'
   ```

   The github token is needed to write to the bruni comment to the PR.

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

## Post-Installation

After the installation steps (either via script or manually) are complete, you must activate the virtual environment in your terminal before running any Python commands.

```bash
source venv310/bin/activate
```

Once activated, you can proceed with running the visual tests as described in the next section.
