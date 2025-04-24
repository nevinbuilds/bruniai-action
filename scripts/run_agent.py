import asyncio
import os
import time
import logging
import argparse
from functools import wraps
from contextlib import asynccontextmanager
import json
from dotenv import load_dotenv
import openai
from openai import RateLimitError
from agents import Agent, Runner
from agents.mcp.server import MCPServerSse, MCPServerSseParams
import requests
from PIL import Image, ImageChops
import numpy as np
import subprocess

# ----------------- Setup -------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-runner")

# Get the GitHub workspace directory for absolute paths
GITHUB_WORKSPACE = os.getenv("GITHUB_WORKSPACE", os.getcwd())
logger.info(f"GitHub workspace: {GITHUB_WORKSPACE}")

def generate_diff_image(before_path, after_path, diff_output_path):
    # Process only local files
    img1 = Image.open(before_path).convert('RGB')
    img2 = Image.open(after_path).convert('RGB')

    # Ensure images have the same dimensions by resizing the second image to match the first
    if img1.size != img2.size:
        logger.warning(f"Image dimensions don't match: {img1.size} vs {img2.size}. Resizing second image.")
        img2 = img2.resize(img1.size)

    # Create a diff image
    diff = ImageChops.difference(img1, img2)

    # Create a mask of non-zero differences
    diff_np = np.array(diff)
    mask = (diff_np != 0).any(axis=2)

    # Convert mask to RGBA format for transparency
    result_np = np.zeros((img1.size[1], img1.size[0], 4), dtype=np.uint8)

    # Set red color with full opacity where differences exist
    result_np[mask, 0] = 255  # R channel
    result_np[mask, 3] = 255  # Alpha channel (fully opaque)

    # Create final image from numpy array
    diff_highlight = Image.fromarray(result_np, 'RGBA')

    # Save the result as PNG to preserve transparency
    diff_highlight.save(diff_output_path, format='PNG')
    logger.info(f"Diff image saved at: {diff_output_path}")

def take_screenshot_with_playwright(url, output_path):
    """Use Playwright directly to take a screenshot."""
    try:
        logger.info(f"Taking screenshot of {url} with Playwright...")
        result = subprocess.run([
            "npx", "playwright", "screenshot",
            "--device", "Desktop Chrome",
            "--full-page",
            url, output_path
        ], capture_output=True, text=True, check=True)
        logger.info(f"Screenshot saved at {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to take screenshot: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error taking screenshot: {e}")
        return False

# ----------------- Post PR Comment -------------------

def get_pr_number_from_event():
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        logger.warning("GITHUB_EVENT_PATH not found.")
        return None

    try:
        with open(event_path, 'r') as f:
            event = json.load(f)

        pr_number = (
            event.get("pull_request", {}).get("number") or
            event.get("issue", {}).get("number")
        )

        if not pr_number:
            logger.warning("PR number not found in event payload.")
        return pr_number
    except Exception as e:
        logger.error("Error reading PR number from event: %s", e)
        return None

def post_pr_comment(summary: str):
    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")  # e.g. 'org/repo'
    pr_number = os.getenv("PR_NUMBER") or get_pr_number_from_event()

    logger.info(f"GITHUB_TOKEN: {github_token}")
    logger.info(f"GITHUB_REPOSITORY: {repo}")
    logger.info(f"PR_NUMBER: {pr_number}")

    if not all([github_token, repo, pr_number]):
        logger.warning("Missing GitHub context, skipping PR comment.")
        return

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.post(url, json={"body": summary}, headers=headers)

    if response.status_code == 201:
        logger.info("📝 Successfully posted PR comment.")
    else:
        logger.error("❌ Failed to post PR comment: %s", response.text)

# ----------------- Rate Limiting Decorator (Optional) -------------------
def rate_limit(calls_per_minute=20):
    min_interval = 60.0 / calls_per_minute
    last_call_time = 0

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_call_time
            now = time.time()
            delta = now - last_call_time
            if delta < min_interval:
                await asyncio.sleep(min_interval - delta)
            last_call_time = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

Runner.run = rate_limit()(Runner.run)

@asynccontextmanager
async def managed_mcp_server():
    mcp_server = None
    try:
        mcp_server = MCPServerSse(params=MCPServerSseParams(url="http://localhost:8931/sse"))
        await mcp_server.connect()
        logger.info("🔌 Connected to MCP server")
        yield mcp_server
    finally:
        if mcp_server:
            try:
                mcp_server.connection = None
                logger.info("🔌 Disconnected MCP server")
            except Exception as e:
                logger.error("Failed to disconnect MCP server: %s", e)

async def run_comparison(mcp_server, agent, prompt):
    try:
        result = await Runner.run(agent, prompt)
        logger.info("✅ Comparison completed.")
        if result.final_output:
            print("\nComparison Results:")
            print(result.final_output)
            return result.final_output
    except Exception as e:
        logger.error("Error during comparison: %s", e)
        raise

async def analyze_sections_side_by_side(mcp_server, base_url, preview_url):
    """Analyze both URLs simultaneously, comparing sections side by side."""
    try:
        logger.info(f"\n{'='*50}\n🔍 Starting side-by-side analysis\n{'='*50}")

        # First identify sections in both URLs
        section_agent = Agent(
            name="Section Analyzer",
            instructions="""Open both URLs in separate tabs and identify all major sections.
            Compare the sections between both URLs directly.

            For each URL:
            1. List all major sections found
            2. Note their position and structure
            3. Compare corresponding sections between URLs
            4. Note any missing or additional sections

            Format the response as:
            ### Base URL Sections:
            [List of sections with positions]

            ### Preview URL Sections:
            [List of sections with positions]

            ### Section Differences:
            - Missing sections in preview: [list]
            - New sections in preview: [list]
            - Sections with different positions: [list]""",
            mcp_servers=[mcp_server]
        )

        section_prompt = f"""Please analyze these two URLs side by side:
        Base URL: {base_url}
        Preview URL: {preview_url}

        Open both in separate tabs and identify all sections."""

        section_result = await Runner.run(section_agent, section_prompt)
        sections_analysis = section_result.final_output
        logger.info(f"\n{'='*50}\n🗺️ Section Analysis:\n{sections_analysis}\n{'='*50}")

        # Now do detailed comparison of each section
        comparison_agent = Agent(
            name="Section Comparator",
            instructions="""Compare each section between the two URLs side by side.
            For each section that exists in either URL:

            1. Visual Comparison:
               - Layout differences (position, size, alignment)
               - Styling differences (colors, fonts, spacing)
               - Responsive behavior differences
               - Visual hierarchy changes

            2. Content Comparison:
               - Text differences
               - Image/media differences
               - Missing or additional elements
               - Content structure changes

            3. Functionality Comparison:
               - Interactive element differences
               - Behavior changes
               - Form/input differences
               - Navigation changes
               - Dynamic content differences

            4. UX & Accessibility Comparison:
               - Focus behavior differences
               - Keyboard navigation changes
               - Error handling differences
               - Loading state differences
               - User feedback differences

            For each section, format the comparison as:
            ### [Section Name] Comparison:

            #### Present In:
            - Base URL: Yes/No
            - Preview URL: Yes/No

            #### Visual Changes:
            - [List specific differences]

            #### Content Changes:
            - [List specific differences]

            #### Functional Changes:
            - [List specific differences]

            #### UX Changes:
            - [List specific differences]

            If a section is missing in either URL, clearly note that and explain the impact.""",
            mcp_servers=[mcp_server]
        )

        comparison_prompt = f"""With both URLs open in separate tabs:
        Base URL: {base_url}
        Preview URL: {preview_url}

        Compare each section side by side following the format in your instructions.
        Pay special attention to:
        1. Sections that exist in one URL but not the other
        2. Sections that have moved positions
        3. Sections with significant content or functional changes

        {sections_analysis}"""

        comparison_result = await Runner.run(comparison_agent, comparison_prompt)
        detailed_comparison = comparison_result.final_output

        logger.info(f"\n{'='*50}\n📊 Detailed Section Comparison:\n{detailed_comparison}\n{'='*50}")

        # Generate final summary
        summary_agent = Agent(
            name="Summary Generator",
            instructions="""Generate a clear, actionable summary of all differences found.
            Categorize changes by severity:

            1. Critical Issues:
               - Missing essential sections
               - Broken core functionality
               - Major content losses
               - Severe layout breaks

            2. Major Changes:
               - Significant layout changes
               - Important content modifications
               - Functional behavior changes
               - UX flow changes

            3. Minor Changes:
               - Small visual differences
               - Minor content updates
               - Style adjustments
               - Non-critical behavior changes

            Format the summary as:
            ### 🚨 Critical Issues
            - [List issues with specific locations and details]

            ### ⚠️ Major Changes
            - [List changes with specific locations and details]

            ### ℹ️ Minor Changes
            - [List changes with specific locations and details]

            ### 📋 Overall Impact Assessment
            [2-3 sentences describing the overall impact of changes]""",
            mcp_servers=[mcp_server]
        )

        summary_prompt = f"""Based on the section analysis and detailed comparison, generate a summary of all changes:

        Section Analysis:
        {sections_analysis}

        Detailed Comparison:
        {detailed_comparison}"""

        summary_result = await Runner.run(summary_agent, summary_prompt)
        final_summary = summary_result.final_output

        logger.info(f"\n{'='*50}\n📝 Final Summary:\n{final_summary}\n{'='*50}")

        return final_summary

    except Exception as e:
        logger.error(f"Error during side-by-side analysis: {e}")
        raise

async def main():
    parser = argparse.ArgumentParser(description='Compare two URLs for visual differences')
    parser.add_argument('--base-url', required=True, help='Base URL to compare against')
    parser.add_argument('--pr-url', required=True, help='PR URL to compare')
    args = parser.parse_args()

    logger.info(f"\n{'='*50}\nStarting URL comparison\nBase URL: {args.base_url}\nPreview URL: {args.pr_url}\n{'='*50}")

    # Ensure the images directory exists in the workspace
    images_dir = os.path.join(GITHUB_WORKSPACE, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Define screenshot paths with absolute paths
    base_screenshot = os.path.join(images_dir, "base_screenshot.png")
    pr_screenshot = os.path.join(images_dir, "pr_screenshot.png")
    diff_output_path = os.path.join(images_dir, "diff.png")

    # Take screenshots with Playwright directly
    base_success = take_screenshot_with_playwright(args.base_url, base_screenshot)
    pr_success = take_screenshot_with_playwright(args.pr_url, pr_screenshot)

    # Generate diff if screenshots were successful
    if base_success and pr_success:
        logger.info("🖼️ Screenshots captured, generating diff image...")
        generate_diff_image(base_screenshot, pr_screenshot, diff_output_path)
        logger.info(f"🔍 Diff image saved at: {diff_output_path}")
    else:
        logger.error("Failed to capture one or both screenshots")
        return

    async with managed_mcp_server() as mcp_server:
        try:
            # Perform side-by-side analysis
            comparison_summary = await analyze_sections_side_by_side(mcp_server, args.base_url, args.pr_url)

            # Try to post to GitHub if possible, otherwise just log
            if os.getenv("GITHUB_TOKEN"):
                post_pr_comment(comparison_summary)
            else:
                logger.info("GitHub environment variables not found. Skipping PR comment.")
                logger.info("Complete analysis has been logged above.")

        except RateLimitError as e:
            logger.error("🚫 Rate limit or quota hit: %s", e)
        except Exception as e:
            logger.exception("❗ Unexpected error occurred")

async def run_main():
    try:
        await main()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error("Fatal error: %s", e)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error("Fatal error: %s", e)
