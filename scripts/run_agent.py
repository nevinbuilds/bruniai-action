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
from openai import OpenAIError, RateLimitError
from agents import Agent, Runner
from agents.mcp.server import MCPServerSse, MCPServerSseParams
import anyio
from anyio import create_task_group, create_memory_object_stream
import requests
from PIL import Image, ImageChops
import numpy as np
import tempfile
from io import BytesIO
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

    # Create a diff image
    diff = ImageChops.difference(img1, img2)

    # Optional: Highlight the diff more (e.g. multiply intensity)
    diff_np = np.array(diff)
    mask = (diff_np != 0).any(axis=2)
    diff_np[mask] = [255, 0, 0]  # Red highlight
    diff_highlight = Image.fromarray(diff_np)

    # Save the result
    diff_highlight.save(diff_output_path)
    print(f"Diff image saved at: {diff_output_path}")

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

async def main():
    parser = argparse.ArgumentParser(description='Compare two URLs for visual differences')
    parser.add_argument('--base-url', required=True, help='Base URL to compare against')
    parser.add_argument('--pr-url', required=True, help='PR URL to compare')
    args = parser.parse_args()

    # Ensure the images directory exists in the workspace
    images_dir = os.path.join(GITHUB_WORKSPACE, "images")
    os.makedirs(images_dir, exist_ok=True)
    logger.info(f"Images directory created at {images_dir}")

    # Define screenshot paths with absolute paths
    base_screenshot = os.path.join(images_dir, "base_screenshot.png")
    pr_screenshot = os.path.join(images_dir, "pr_screenshot.png")
    diff_output_path = os.path.join(images_dir, "diff.png")

    logger.info(f"Base screenshot path: {base_screenshot}")
    logger.info(f"PR screenshot path: {pr_screenshot}")
    logger.info(f"Diff output path: {diff_output_path}")

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
            agent = Agent(
                name="URL Comparator",
                instructions="""Compare two webpages and report any significant differences.
                1. First visit the base URL and analyze its content
                2. Then visit the PR URL and compare it with the base URL
                3. Report any significant differences in layout, content, or functionality""",
                mcp_servers=[mcp_server]
            )

            prompt = f"""Please compare these two URLs and report any significant differences:
            Base URL: {args.base_url}
            PR URL: {args.pr_url}

            Focus on:
            - Visual layout changes
            - Content differences
            - Functional changes
            - Any broken elements or errors

            Provide a detailed comparison report."""

            logger.info("🧠 Starting comparison between URLs")
            logger.info("Base URL: %s", args.base_url)
            logger.info("PR URL: %s", args.pr_url)

            comparison_summary = await run_comparison(mcp_server, agent, prompt)
            if comparison_summary:
                post_pr_comment(f"### 🔍 PR Comparison Summary\n\n{comparison_summary}")

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
