import subprocess
import logging
import asyncio
from playwright.async_api import async_playwright

logger = logging.getLogger("agent-runner")

def take_screenshot_with_playwright(url, output_path):
    """Use Playwright directly to take a screenshot."""
    try:
        logger.info(f"Taking screenshot of {url} with Playwright...")
        result = subprocess.run([
            "npx", "playwright", "screenshot",
            "--browser", "chromium",
            "--device", "Desktop Chrome",
            "--full-page",
            url, output_path
        ], capture_output=True, text=True, check=True)
        logger.info(f"Screenshot saved at {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to take screenshot: {e.stderr}")
        # Print detailed output to help with debugging
        logger.error(f"Command output: {e.stdout}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error taking screenshot: {e}")
        return False

async def take_section_screenshot_with_playwright(url, output_path, bounding_box):
    """Take a screenshot of a specific section using Playwright's clip parameter.

    Args:
        url: URL to screenshot
        output_path: Path to save the screenshot
        bounding_box: Dict with x, y, width, height coordinates

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Taking section screenshot of {url} with bounding box {bounding_box}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Take screenshot with clip parameter
            await page.screenshot(
                path=output_path,
                clip={
                    "x": bounding_box["x"],
                    "y": bounding_box["y"],
                    "width": bounding_box["width"],
                    "height": bounding_box["height"]
                }
            )

            await browser.close()
            logger.info(f"Section screenshot saved at {output_path}")
            return True

    except Exception as e:
        logger.error(f"Failed to take section screenshot: {e}")
        return False
