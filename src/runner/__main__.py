import asyncio
import os
import sys
import logging
import argparse
import json
from dotenv import load_dotenv
import openai
from openai import RateLimitError
import base64

# Add the src directory to the Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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

# Import agents after setting up the path
from agents import Agent, Runner

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
    parser.add_argument('--pages', required=False, help='JSON array of page paths to test (e.g., ["/", "/about", "/contact"]) or comma-separated paths (e.g., "/,/about,/contact"). If not provided, only the homepage is tested.')
    parser.add_argument('--bruni-token', required=False, help='Token for Bruni API (overrides BRUNI_TOKEN from .env)')
    parser.add_argument('--bruni-api-url', required=False, help='URL for Bruni API (overrides BRUNI_API_URL from .env)')
    args = parser.parse_args()

    # Parse pages configuration
    pages = ['/']  # Default to homepage only
    if args.pages:
        try:
            # Clean up the input string - remove any extra whitespace or quotes
            pages_input = args.pages.strip()

            # If the input looks like it might be wrapped in extra quotes, try to clean it
            if pages_input.startswith('"') and pages_input.endswith('"'):
                pages_input = pages_input[1:-1]

            # Check if it looks like JSON (starts with [ and ends with ])
            if pages_input.startswith('[') and pages_input.endswith(']'):
                # Try to parse as JSON
                pages = json.loads(pages_input)
            else:
                # Try to parse as comma-separated values
                pages = [page.strip() for page in pages_input.split(',') if page.strip()]
                if not pages:
                    logger.error("No valid page paths found in comma-separated input")
                    return

            if not isinstance(pages, list):
                logger.error("Pages parameter must be a JSON array or comma-separated list")
                logger.error(f"Received: {type(pages)} - {pages}")
                return

            logger.info(f"Testing {len(pages)} pages: {pages}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in pages parameter: {e}")
            logger.error(f"Raw input: '{args.pages}'")
            logger.error("Expected format: '[\"/\", \"/about\", \"/contact\"]' or '/,/about,/contact'")
            return
        except Exception as e:
            logger.error(f"Unexpected error parsing pages parameter: {e}")
            logger.error(f"Raw input: '{args.pages}'")
            return
    else:
        logger.info("No pages specified, testing homepage only")

    logger.info(f"\n{'='*50}\nStarting URL comparison\nBase URL: {args.base_url}\nPreview URL: {args.pr_url}\nPages: {pages}\n{'='*50}")

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

    # Process each page
    all_results = []
    for i, page_path in enumerate(pages):
        logger.info(f"\n{'='*30}\nProcessing page {i+1}/{len(pages)}: {page_path}\n{'='*30}")

        # Construct full URLs for this page
        base_url = args.base_url.rstrip('/') + page_path
        pr_url = args.pr_url.rstrip('/') + page_path

        logger.info(f"Base URL: {base_url}")
        logger.info(f"PR URL: {pr_url}")

        # Define screenshot paths with page-specific names
        page_suffix = page_path.replace('/', '_').replace('_', '') or 'home'
        base_screenshot = os.path.join(images_dir, f"base_screenshot_{page_suffix}.png")
        pr_screenshot = os.path.join(images_dir, f"pr_screenshot_{page_suffix}.png")
        diff_output_path = os.path.join(images_dir, f"diff_{page_suffix}.png")

        # Take screenshots with Playwright directly
        base_success = take_screenshot_with_playwright(base_url, base_screenshot)
        pr_success = take_screenshot_with_playwright(pr_url, pr_screenshot)

        if not (base_success and pr_success):
            logger.error(f"Failed to capture screenshots for page: {page_path}")
            continue

        # Extract section bounding boxes from the base URL for this page
        sections = await extract_section_bounding_boxes(base_url)
        logger.info(f"Extracted {len(sections)} sections from {base_url}")
        # Optionally, save to a file for inspection
        with open(os.path.join(images_dir, f"sections_{page_suffix}.json"), "w") as f:
            json.dump(sections, f, indent=2)

        # Continue with diff generation, etc.
        logger.info("🖼️ Screenshots captured, generating diff image...")
        generate_diff_image(base_screenshot, pr_screenshot, diff_output_path)
        logger.info(f"🔍 Diff image saved at: {diff_output_path}")

        # Store page result for later processing
        page_result = {
            'page_path': page_path,
            'base_url': base_url,
            'pr_url': pr_url,
            'base_screenshot': base_screenshot,
            'pr_screenshot': pr_screenshot,
            'diff_output_path': diff_output_path,
            'sections': sections
        }
        all_results.append(page_result)

    # Process all pages with analysis
    async with managed_mcp_server() as mcp_server:
        try:
            all_analyses = []
            for page_result in all_results:
                logger.info(f"\n{'='*30}\nAnalyzing page: {page_result['page_path']}\n{'='*30}")

                # First get the sections analysis
                sections_analysis = await analyze_sections_side_by_side(mcp_server, page_result['base_url'], page_result['pr_url'])

                # Then perform visual analysis with the sections information
                visual_analysis = await analyze_images_with_vision(
                    page_result['base_screenshot'],
                    page_result['pr_screenshot'],
                    page_result['diff_output_path'],
                    page_result['base_url'],
                    page_result['pr_url'],
                    pr_number,
                    repo,
                    sections_analysis,
                    pr_title=pr_title,
                    pr_description=pr_description
                )

                # Store the analysis results
                page_analysis = {
                    'page_path': page_result['page_path'],
                    'sections_analysis': sections_analysis,
                    'visual_analysis': visual_analysis
                }
                all_analyses.append(page_analysis)

            # Combine all analyses into a comprehensive report
            if len(all_analyses) == 1:
                # Single page - use the original format
                page_analysis = all_analyses[0]
                formatted_visual_analysis = format_visual_analysis_to_markdown(page_analysis['visual_analysis'])
                final_summary = (
                    "Information about visual testing analysis provided by [bruniai](https://www.brunivisual.com/)\n\n"
                    "<details>\n"
                    "<summary>Structural Analysis</summary>\n\n"
                    f"{page_analysis['sections_analysis']}\n"
                    "</details>\n\n"
                    f"{formatted_visual_analysis}"
                )
            else:
                # Multiple pages - create a comprehensive report
                final_summary = (
                    "Information about visual testing analysis provided by [bruniai](https://www.brunivisual.com/)\n\n"
                    f"**Testing Summary**: {len(all_analyses)} pages analyzed\n\n"
                )

                for i, page_analysis in enumerate(all_analyses, 1):
                    page_path = page_analysis['page_path']
                    visual_analysis = page_analysis['visual_analysis']
                    sections_analysis = page_analysis['sections_analysis']

                    # Format the visual analysis for this page
                    formatted_visual_analysis = format_visual_analysis_to_markdown(visual_analysis)

                    # Add page-specific section
                    page_summary = (
                        f"<details>\n"
                        f"<summary>Page {i}: {page_path}</summary>\n\n"
                        f"<details>\n"
                        f"<summary>Structural Analysis</summary>\n\n"
                        f"{sections_analysis}\n"
                        f"</details>\n\n"
                        f"{formatted_visual_analysis}\n"
                        f"</details>\n\n"
                    )
                    final_summary += page_summary

            # Send report to Bruni API if configured and get the report URL
            report_url = None
            if bruni_reporter and len(all_analyses) == 1:
                # For single page, send report as before
                try:
                    page_analysis = all_analyses[0]
                    page_result = all_results[0]

                    # Encode images to base64
                    def encode_image(image_path: str) -> str:
                        with open(image_path, "rb") as image_file:
                            return base64.b64encode(image_file.read()).decode('utf-8')

                    # Create image references with base64 data
                    image_refs = {
                        "base_screenshot": encode_image(page_result['base_screenshot']),
                        "pr_screenshot": encode_image(page_result['pr_screenshot']),
                        "diff_image": encode_image(page_result['diff_output_path'])
                    }

                    # Create report with images
                    report_data = parse_analysis_results(
                        page_result['base_url'],
                        page_result['pr_url'],
                        pr_number,
                        repo,
                        page_analysis['visual_analysis'],
                        image_refs=image_refs
                    )

                    # Send report with images
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
            elif bruni_reporter and len(all_analyses) > 1:
                # For multiple pages, log that we're not sending to Bruni API yet
                logger.info("Multi-page testing detected. Bruni API reporting for multiple pages not yet implemented.")

            # Update the final summary with report URL if available (for single page)
            if len(all_analyses) == 1 and report_url:
                page_analysis = all_analyses[0]
                formatted_visual_analysis = format_visual_analysis_to_markdown(page_analysis['visual_analysis'], report_url)
                final_summary = (
                    "Information about visual testing analysis provided by [bruniai](https://www.brunivisual.com/)\n\n"
                    "<details>\n"
                    "<summary>Structural Analysis</summary>\n\n"
                    f"{page_analysis['sections_analysis']}\n"
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
