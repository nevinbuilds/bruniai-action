import asyncio
import os
import logging
import argparse
import json
from dotenv import load_dotenv
import openai
from openai import RateLimitError
from agents import Agent, Runner
import base64

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
    parser.add_argument('--pages', required=False, help='JSON array of relative URLs for multi-page testing (e.g., ["/about", "/contact"])')
    args = parser.parse_args()

    pages_to_process = []
    if args.pages:
        try:
            pages_data = json.loads(args.pages)
            
            if isinstance(pages_data, list) and all(isinstance(item, str) for item in pages_data):
                base_url = args.base_url.rstrip('/')
                pr_url = args.pr_url.rstrip('/')
                
                for relative_path in pages_data:
                    if not relative_path.startswith('/'):
                        relative_path = '/' + relative_path
                    
                    page_name = relative_path.strip('/').replace('/', ' ').title() or 'Homepage'
                    if page_name == '':
                        page_name = 'Homepage'
                    
                    pages_to_process.append({
                        'base_url': base_url + relative_path,
                        'pr_url': pr_url + relative_path,
                        'name': page_name
                    })
            
            elif isinstance(pages_data, list) and all(isinstance(item, dict) for item in pages_data):
                for page in pages_data:
                    pages_to_process.append({
                        'base_url': page['base_url'],
                        'pr_url': page['pr_url'],
                        'name': page.get('name', f"Page {len(pages_to_process) + 1}")
                    })
            else:
                logger.error("Invalid pages format. Expected array of strings (relative URLs) or array of objects (legacy format)")
                return
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid pages JSON format: {e}")
            return
    else:
        pages_to_process.append({
            'base_url': args.base_url,
            'pr_url': args.pr_url,
            'name': 'Homepage'
        })

    logger.info(f"\n{'='*50}\nStarting URL comparison for {len(pages_to_process)} page(s)\n{'='*50}")

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

    page_results = []
    async with managed_mcp_server() as mcp_server:
        for page_info in pages_to_process:
            try:
                result = await process_single_page(page_info, images_dir, mcp_server, pr_title, pr_description, pr_number, repo)
                if result:
                    page_results.append(result)
            except Exception as e:
                logger.error(f"Error processing {page_info['name']}: {e}")
                continue

    if not page_results:
        logger.error("No pages were successfully processed")
        return

    aggregated_analysis = aggregate_page_results(page_results)

    # Send report to Bruni API if configured
    report_url = None
    if bruni_reporter:
        try:
            combined_image_refs = {}
            for i, result in enumerate(page_results):
                page_prefix = f"page_{i}"
                combined_image_refs[f"{page_prefix}_base"] = encode_image(result['screenshots']['base'])
                combined_image_refs[f"{page_prefix}_pr"] = encode_image(result['screenshots']['pr'])
                combined_image_refs[f"{page_prefix}_diff"] = encode_image(result['screenshots']['diff'])

            report_data = parse_analysis_results(
                page_results[0]['base_url'],  # Use first page as primary
                page_results[0]['pr_url'],
                pr_number,
                repo,
                aggregated_analysis,
                image_refs=combined_image_refs
            )

            api_response = await bruni_reporter.send_report(report_data)
            if api_response and "id" in api_response:
                report_id = api_response["id"]
                base_api_url = bruni_api_url.replace("/api/reports", "").rstrip("/")
                report_url = f"{base_api_url}/report/{report_id}"
                logger.info(f"Report available at: {report_url}")
        except Exception as e:
            logger.error(f"Failed to send report to Bruni API: {e}")

    final_summary = format_multi_page_summary(page_results, report_url)

    # Post to GitHub
    post_pr_comment(final_summary)
    logger.info("Multi-page analysis complete")

async def process_single_page(page_info, images_dir, mcp_server, pr_title, pr_description, pr_number, repo):
    """Process a single page comparison and return the analysis results."""
    base_url = page_info['base_url']
    pr_url = page_info['pr_url']
    page_name = page_info['name']
    
    logger.info(f"Processing {page_name}: {base_url} vs {pr_url}")
    
    # Define screenshot paths with page-specific names
    safe_name = "".join(c for c in page_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_').lower()
    
    base_screenshot = os.path.join(images_dir, f"{safe_name}_base_screenshot.png")
    pr_screenshot = os.path.join(images_dir, f"{safe_name}_pr_screenshot.png")
    diff_output_path = os.path.join(images_dir, f"{safe_name}_diff.png")
    
    # Take screenshots
    base_success = take_screenshot_with_playwright(base_url, base_screenshot)
    pr_success = take_screenshot_with_playwright(pr_url, pr_screenshot)
    
    if not (base_success and pr_success):
        logger.error(f"Failed to capture screenshots for {page_name}")
        return None
    
    # Extract section bounding boxes
    sections = await extract_section_bounding_boxes(base_url)
    logger.info(f"Extracted {len(sections)} sections from {page_name}")
    
    generate_diff_image(base_screenshot, pr_screenshot, diff_output_path)
    
    sections_analysis = await analyze_sections_side_by_side(mcp_server, base_url, pr_url)
    visual_analysis = await analyze_images_with_vision(
        base_screenshot,
        pr_screenshot,
        diff_output_path,
        base_url,
        pr_url,
        pr_number,
        repo,
        sections_analysis,
        pr_title=pr_title,
        pr_description=pr_description
    )
    
    return {
        'page_name': page_name,
        'base_url': base_url,
        'pr_url': pr_url,
        'visual_analysis': visual_analysis,
        'sections_analysis': sections_analysis,
        'screenshots': {
            'base': base_screenshot,
            'pr': pr_screenshot,
            'diff': diff_output_path
        }
    }

def aggregate_page_results(page_results):
    """Aggregate multiple page results into a single analysis."""
    overall_status = "pass"
    critical_issues_found = False
    significant_changes_found = False
    
    for result in page_results:
        analysis = result['visual_analysis']
        if analysis.get('status_enum') == 'fail':
            overall_status = "fail"
            critical_issues_found = True
        elif analysis.get('status_enum') == 'warning' and overall_status != 'fail':
            overall_status = "warning"
            significant_changes_found = True
    
    return {
        'status_enum': overall_status,
        'critical_issues_enum': 'missing_sections' if critical_issues_found else 'none',
        'visual_changes_enum': 'significant' if significant_changes_found else 'minor',
        'recommendation_enum': 'reject' if overall_status == 'fail' else ('review_required' if overall_status == 'warning' else 'pass'),
        'conclusion': {
            'summary': f"Analysis completed for {len(page_results)} page(s). Overall status: {overall_status}"
        }
    }

def format_multi_page_summary(page_results, report_url=None):
    """Format multiple page results into a GitHub comment."""
    summary_parts = [
        "Information about visual testing analysis provided by [bruniai](https://www.brunivisual.com/)\n\n"
    ]
    
    if report_url:
        summary_parts.append(f"📊 [View detailed report]({report_url})\n\n")
    
    summary_parts.append(f"## Multi-Page Visual Analysis ({len(page_results)} pages tested)\n\n")
    
    for i, result in enumerate(page_results, 1):
        analysis = result['visual_analysis']
        page_name = result['page_name']
        status_emoji = "✅" if analysis.get('status_enum') == 'pass' else ("⚠️" if analysis.get('status_enum') == 'warning' else "❌")
        
        summary_parts.append(f"### {status_emoji} {page_name}\n")
        summary_parts.append(f"**Base URL:** {result['base_url']}\n")
        summary_parts.append(f"**PR URL:** {result['pr_url']}\n\n")
        
        formatted_analysis = format_visual_analysis_to_markdown(analysis, report_url)
        summary_parts.append("<details>\n")
        summary_parts.append(f"<summary>View {page_name} Analysis</summary>\n\n")
        summary_parts.append(f"{result['sections_analysis']}\n\n")
        summary_parts.append(f"{formatted_analysis}\n")
        summary_parts.append("</details>\n\n")
    
    return "".join(summary_parts)

def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

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
