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
import base64

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

    # Instead of resizing, create new white images with maximum dimensions
    max_width = max(img1.size[0], img2.size[0])
    max_height = max(img1.size[1], img2.size[1])

    # Create white background images
    new_img1 = Image.new('RGB', (max_width, max_height), 'white')
    new_img2 = Image.new('RGB', (max_width, max_height), 'white')

    # Paste original images onto white backgrounds (this will preserve their original sizes)
    new_img1.paste(img1, (0, 0))
    new_img2.paste(img2, (0, 0))

    # Save transformed images.
    new_img1.save(before_path.replace('.png', '-resized.png'))
    new_img2.save(after_path.replace('.png', '-resized.png'))

    # Create a diff image
    diff = ImageChops.difference(new_img1, new_img2)

    # Create a mask of non-zero differences
    diff_np = np.array(diff)
    mask = (diff_np != 0).any(axis=2)

    # Convert mask to RGBA format for transparency
    result_np = np.zeros((max_height, max_width, 4), dtype=np.uint8)

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

async def analyze_images_with_vision(base_screenshot: str, pr_screenshot: str, diff_image: str, sections_analysis: str = None):
    """Analyze screenshots using GPT-4 Vision API to identify visual differences."""
    logger.info(f"\n{'='*50}\n🔍 Starting image-based analysis\n{'='*50}")

    try:
        # Encode images to base64
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        base64_base = encode_image(base_screenshot.replace('.png', '-resized.png'))
        base64_pr = encode_image(pr_screenshot.replace('.png', '-resized.png'))
        base64_diff = encode_image(diff_image)

        # Create OpenAI client
        client = openai.OpenAI()

        # Prepare the messages for GPT-4 Vision
        messages = [
            {
                "role": "system",
                "content": """
                    You are a system designed to identify structural and visual changes in websites for testing purposes. Your primary responsibility is to detect and report significant structural changes, with a particular focus on missing or altered sections.

                    CRITICAL CHECKS (Must be performed first):
                    1. MISSING SECTIONS CHECK: Compare the base image with the PR image and the diff image and immediately identify if any sections are completely missing
                       - A missing section is a CRITICAL issue and should be reported prominently
                       - This check must be performed before any other analysis
                       - If a section exists in the base image and section analysis but not in the PR image, this is a critical failure
                       - Use the sections analysis to guide your decisions, the analysis will be delimited by <<<>>>.
                       - If the section animates or moves make sure to point it out and take in consideration to not flag as visual regression on things that are animating.

                    2. STRUCTURAL CHANGES CHECK:
                       - Identify if sections have moved positions
                       - Check if the overall layout structure has changed
                       - Verify if major UI components have been relocated
                       - These are considered significant issues
                       - Use the sections analysis to guide your analysis, the analysis will be delimited by ###.

                    3. VISUAL HIERARCHY CHECK:
                       - Verify if the visual hierarchy of elements remains consistent
                       - Check if important UI elements maintain their relative positioning
                       - Ensure navigation elements remain accessible
                       - Use the sections analysis to guide your analysis, the analysis will be delimited by ###.

                    NON-CRITICAL CHANGES (Should be noted but not flagged as issues):
                    - Text content changes
                    - Menu item text updates
                    - Headline modifications
                    - Product information updates
                    - Price changes
                    - Minor styling changes that don't affect layout

                    FORMAT YOUR RESPONSE AS FOLLOWS:
                    1. CRITICAL ISSUES (if any):
                       - List any missing sections
                       - List any major structural changes
                       - List any broken layouts

                    2. STRUCTURAL ANALYSIS:
                       - Compare each section's presence and position
                       - Note any layout modifications

                    3. VISUAL CHANGES:
                       - Document non-critical changes
                       - Note any styling updates

                    4. CONCLUSION:
                       - Clearly state if there are any critical issues
                       - Even if there are not critical issues, always describe where any visual changes are and why they are not critical.
                       - Provide a pass/fail recommendation
                """
            }
        ]

        if sections_analysis:
            messages.append({
                "role": "user",
                "content": f"Here is the structural analysis of the website's sections that you should use to guide your visual analysis<<<:\n\n{sections_analysis}>>>"
            })

        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here are the images to analyze in the right order. Base Image, PR Image and Diff Image."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_base}"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_pr}"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_diff}"
                    }
                }
            ]
        })

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            max_tokens=1000,
            temperature=0.2  # Lower temperature for more consistent analysis
        )

        analysis = response.choices[0].message.content
        logger.info(f"\n{'='*50}\n🎨 Visual Analysis Results:\n{analysis}\n{'='*50}")
        return analysis

    except Exception as e:
        logger.error(f"Error during image analysis: {e}")
        return f"Error performing image analysis: {str(e)}"

async def analyze_sections_side_by_side(mcp_server, base_url, preview_url):
    """Analyze the base URL to identify its sections structure."""
    try:
        logger.info(f"\n{'='*50}\n🔍 Starting base URL section analysis\n{'='*50}")

        # Identify sections in the base URL
        section_agent = Agent(
            name="Section Analyzer",
            instructions="""Analyze the base URL and identify all major sections.
            This will serve as our reference structure for visual comparison.

            For the base URL:
            1. List all major sections found
            2. Note their position and structure
            3. Describe the purpose of each section
            4. Note any important visual elements or patterns
            5. Note if the section animates or moves. This is important as it should probably be ignored.
            Format the response as:
            ### Base URL Structure:
            [Overall layout description]

            ### Sections (in order of appearance):
            1. [Section Name]
               - Position: [description]
               - Purpose: [description]
               - Key Elements: [list]
               - Visual Patterns: [description]
               - Animation : [description]

            2. [Section Name]
               ...

            This structural information will be used as a reference to analyze visual changes in the preview URL.""",
            mcp_servers=[mcp_server]
        )

        section_prompt = f"""Please analyze this base URL to establish our reference structure:
        Base URL: {base_url}

        Focus on identifying all major sections and their characteristics.
        This will serve as our baseline for comparing visual changes."""

        section_result = await Runner.run(section_agent, section_prompt)
        sections_analysis = section_result.final_output
        logger.info(f"\n{'='*50}\n🗺️ Base URL Section Analysis:\n{sections_analysis}\n{'='*50}")

        return sections_analysis

    except Exception as e:
        logger.error(f"Error during section analysis: {e}")
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

    if not (base_success and pr_success):
        logger.error("Failed to capture one or both screenshots")
        return

    logger.info("🖼️ Screenshots captured, generating diff image...")
    generate_diff_image(base_screenshot, pr_screenshot, diff_output_path)
    logger.info(f"🔍 Diff image saved at: {diff_output_path}")

    async with managed_mcp_server() as mcp_server:
        try:
            # First get the sections analysis
            sections_analysis = await analyze_sections_side_by_side(mcp_server, args.base_url, args.pr_url)

            # Then perform visual analysis with the sections information
            visual_analysis = await analyze_images_with_vision(base_screenshot, pr_screenshot, diff_output_path, sections_analysis)

            # Combine both analyses
            final_summary = f"""# URL Comparison Analysis

            ## Structural Analysis
            {sections_analysis}

            ## Visual Analysis
            {visual_analysis}"""

            # Try to post to GitHub if possible, otherwise just log
            if os.getenv("GITHUB_TOKEN"):
                post_pr_comment(final_summary)
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
