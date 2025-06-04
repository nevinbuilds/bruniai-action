import asyncio
import os
import logging
import argparse
import json
from dotenv import load_dotenv
import openai
from openai import RateLimitError
from agents import Agent, Runner

# Import from our modules
from playwright_utils.screenshot import take_screenshot_with_playwright
from playwright_utils.bounding_boxes import extract_section_bounding_boxes
from github.pr_comments import post_pr_comment, format_visual_analysis_to_markdown
from image_processing.diff import generate_diff_image
from analysis.vision import analyze_images_with_vision
from analysis.sections import analyze_sections_side_by_side
from core.mcp import managed_mcp_server
from core.rate_limit import rate_limit
from github.pr_metadata import fetch_pr_metadata
from reporter.reporter import BruniReporter
from reporter.report_generator import parse_analysis_results
from github.pr_comments import get_pr_number_from_event

# ----------------- Setup -------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-runner")

# Get the GitHub workspace directory for absolute paths
GITHUB_WORKSPACE = os.getenv("GITHUB_WORKSPACE", os.getcwd())
logger.info(f"GitHub workspace: {GITHUB_WORKSPACE}")

# Apply rate limiting to Runner.run
Runner.run = rate_limit()(Runner.run)

async def main():
    parser = argparse.ArgumentParser(description='Compare two URLs for visual differences')
    parser.add_argument('--base-url', required=True, help='Base URL to compare against')
    parser.add_argument('--pr-url', required=True, help='PR URL to compare')
    parser.add_argument('--bruni-token', required=False, help='Token for Bruni API (overrides BRUNI_TOKEN from .env)')
    parser.add_argument('--bruni-api-url', required=False, help='URL for Bruni API (overrides BRUNI_API_URL from .env)')
    args = parser.parse_args()

    logger.info(f"\n{'='*50}\nStarting URL comparison\nBase URL: {args.base_url}\nPreview URL: {args.pr_url}\n{'='*50}")

    # Get PR information from GitHub environment variables
    pr_title, pr_description = fetch_pr_metadata()
    repo = os.getenv("GITHUB_REPOSITORY")  # e.g. 'org/repo'
    pr_number = os.getenv("PR_NUMBER") or get_pr_number_from_event()

    logger.info(f"PR Title: {pr_title}")
    logger.info(f"PR Description: {pr_description}")

    # Initialize Bruni reporter if token is provided (either from .env or command line)
    bruni_token = args.bruni_token or os.getenv("BRUNI_TOKEN")
    bruni_api_url = args.bruni_api_url or os.getenv("BRUNI_API_URL", "https://bruniai-app.vercel.app/api/reports")

    bruni_reporter = None
    if bruni_token:
        bruni_reporter = BruniReporter(
            bruni_token,
            bruni_api_url
        )
        logger.info("Bruni reporter initialized")
    else:
        logger.info("No Bruni token provided (neither in .env nor as argument), reporting will be skipped")

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

    # Extract section bounding boxes from the base URL
    sections = await extract_section_bounding_boxes(args.base_url)
    logger.info(f"Extracted {len(sections)} sections from base URL")
    # Optionally, save to a file for inspection
    with open(os.path.join(images_dir, "sections.json"), "w") as f:
        json.dump(sections, f, indent=2)

    # Continue with diff generation, etc.
    logger.info("🖼️ Screenshots captured, generating diff image...")
    generate_diff_image(base_screenshot, pr_screenshot, diff_output_path)
    logger.info(f"🔍 Diff image saved at: {diff_output_path}")

    async with managed_mcp_server() as mcp_server:
        try:
            # First get the sections analysis
            sections_analysis = await analyze_sections_side_by_side(mcp_server, args.base_url, args.pr_url)

            # Then perform visual analysis with the sections information
            visual_analysis = await analyze_images_with_vision(
                base_screenshot,
                pr_screenshot,
                diff_output_path,
                args.base_url,
                args.pr_url,
                pr_number,
                repo,
                sections_analysis,
                pr_title=pr_title,
                pr_description=pr_description
            )

            # Combine both analyses
            formatted_visual_analysis = format_visual_analysis_to_markdown(visual_analysis)
            final_summary = (
                "Information about visual testing analysis provided by [bruniai](https://www.brunivisual.com/)\n\n"
                "<details>\n"
                "<summary>Structural Analysis</summary>\n\n"
                f"{sections_analysis}\n"
                "</details>\n\n"
                f"{formatted_visual_analysis}"
            )

            # Send report to Bruni API if configured and get the report URL
            report_url = None
            if bruni_reporter:
                try:
                    report_data = parse_analysis_results(
                        args.base_url,
                        args.pr_url,
                        pr_number,
                        repo,
                        visual_analysis,
                    )
                    api_response = await bruni_reporter.send_report(report_data)

                    # Extract report ID from API response and construct URL
                    if api_response and "id" in api_response:
                        report_id = api_response["id"]
                        # Remove the /api/reports part and add /reports/{id}
                        base_api_url = bruni_api_url.replace("/api/reports", "").rstrip("/")
                        report_url = f"{base_api_url}/report/{report_id}"
                        logger.info(f"Report available at: {report_url}")
                    else:
                        logger.warning(f"No report ID found in API response: {api_response}")
                        logger.debug(f"Full API response: {api_response}")

                except Exception as e:
                    logger.error(f"Failed to send report to Bruni API: {e}")

            # Now format the visual analysis with the report URL if available
            formatted_visual_analysis = format_visual_analysis_to_markdown(visual_analysis, report_url)
            final_summary = (
                "Information about visual testing analysis provided by [bruniai](https://www.brunivisual.com/)\n\n"
                "<details>\n"
                "<summary>Structural Analysis</summary>\n\n"
                f"{sections_analysis}\n"
                "</details>\n\n"
                f"{formatted_visual_analysis}"
            )

            # Post to GitHub
            post_pr_comment(final_summary)
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
