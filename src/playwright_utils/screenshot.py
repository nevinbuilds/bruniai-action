import subprocess
import logging

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
