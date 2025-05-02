# Getting Started

This guide will help you set up and start using the Visual Regression Testing tool locally using python.

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

4. **Install Playwright MCP**

   ```bash
   npm install -g @playwright/mcp
   ```

5. **Set Up Environment Variables**
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Visual Tests

1. **Start the MCP Server**

   ```bash
   npx @playwright/mcp@latest --port 8931
   ```

2. **Run the Visual Regression Tests**

   ```bash
   python3 -m src.runner --base-url <production-url> --pr-url <pull-request-url>
   ```

   Example:

   ```bash
   python3 -m src.runner --base-url https://www.brunivisual.com/ --pr-url https://bruni-website-git-actionexp-nevinbuilds.vercel.app
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
