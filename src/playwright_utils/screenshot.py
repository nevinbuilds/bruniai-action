import subprocess
import logging
import asyncio
from playwright.async_api import async_playwright
from .bounding_boxes import parse_section_data_from_analysis

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

async def take_section_screenshot_by_selector(url, output_path, section_id, sections_analysis):
    """Take a screenshot of a specific section using its ID and analysis data.

    Args:
        url: URL to screenshot
        output_path: Path to save the screenshot
        section_id: The section ID to target
        sections_analysis: The sections analysis data containing section information

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Taking section screenshot of {url} for section ID: {section_id}")

        # Parse the sections analysis to get the section data
        sections_data = parse_section_data_from_analysis(sections_analysis)

        # Find the section with the matching ID
        target_section = None
        for section in sections_data:
            if section['section_id'] == section_id:
                target_section = section
                break

        if not target_section:
            logger.error(f"Section ID {section_id} not found in analysis")
            return False

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Build selector by combining element tag, ID, and classes for maximum specificity
            selector_parts = []

            # Start with the HTML element tag
            if target_section.get('html_element'):
                selector_parts.append(target_section['html_element'])
            else:
                # Fallback to generic section tags
                selector_parts.append("section,header,footer,main,nav,aside,article")

            # Add HTML ID if available (most specific)
            if target_section.get('html_id'):
                selector_parts.append(f"#{target_section['html_id']}")

            # Add ALL HTML classes for maximum specificity
            if target_section.get('html_classes'):
                classes = target_section['html_classes'].split()
                # Escape special characters in class names for valid CSS selectors
                escaped_classes = []
                for cls in classes:
                    # Properly escape CSS selector special characters
                    # Escape: [ ] ( ) { } : ; , . ! @ # $ % ^ & * + = | \ / ~ ` " ' < > ? space
                    escaped_cls = cls.replace('\\', '\\\\')  # Escape backslashes first
                    escaped_cls = escaped_cls.replace('[', '\\[')
                    escaped_cls = escaped_cls.replace(']', '\\]')
                    escaped_cls = escaped_cls.replace('(', '\\(')
                    escaped_cls = escaped_cls.replace(')', '\\)')
                    escaped_cls = escaped_cls.replace('{', '\\{')
                    escaped_cls = escaped_cls.replace('}', '\\}')
                    escaped_cls = escaped_cls.replace(':', '\\:')
                    escaped_cls = escaped_cls.replace(';', '\\;')
                    escaped_cls = escaped_cls.replace(',', '\\,')
                    escaped_cls = escaped_cls.replace('.', '\\.')
                    escaped_cls = escaped_cls.replace('!', '\\!')
                    escaped_cls = escaped_cls.replace('@', '\\@')
                    escaped_cls = escaped_cls.replace('#', '\\#')
                    escaped_cls = escaped_cls.replace('$', '\\$')
                    escaped_cls = escaped_cls.replace('%', '\\%')
                    escaped_cls = escaped_cls.replace('^', '\\^')
                    escaped_cls = escaped_cls.replace('&', '\\&')
                    escaped_cls = escaped_cls.replace('*', '\\*')
                    escaped_cls = escaped_cls.replace('+', '\\+')
                    escaped_cls = escaped_cls.replace('=', '\\=')
                    escaped_cls = escaped_cls.replace('|', '\\|')
                    escaped_cls = escaped_cls.replace('/', '\\/')
                    escaped_cls = escaped_cls.replace('~', '\\~')
                    escaped_cls = escaped_cls.replace('`', '\\`')
                    escaped_cls = escaped_cls.replace('"', '\\"')
                    escaped_cls = escaped_cls.replace("'", "\\'")
                    escaped_cls = escaped_cls.replace('<', '\\<')
                    escaped_cls = escaped_cls.replace('>', '\\>')
                    escaped_cls = escaped_cls.replace('?', '\\?')
                    escaped_cls = escaped_cls.replace(' ', '\\ ')  # Escape spaces
                    escaped_classes.append(f".{escaped_cls}")
                selector_parts.extend(escaped_classes)

            # Combine all parts into a single selector
            selector = ''.join(selector_parts)
            logger.info(f"Using combined selector: {selector}")

            # Find the element and get its bounding box
            element = await page.query_selector(selector)
            if not element:
                logger.warning(f"Element not found with selector: {selector}, taking full page screenshot")
                # Fallback to taking full page screenshot
                await page.screenshot(path=output_path)
            else:
                # Get the bounding box of the element
                bounding_box = await element.bounding_box()
                if bounding_box:
                    logger.info(f"Found element with bounding box: {bounding_box}")

                    # Get page dimensions for validation
                    page_size = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
                    page_content_size = await page.evaluate("() => ({ width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight })")
                    logger.info(f"Page viewport: {page_size}, content size: {page_content_size}")

                    # Check if element is in viewport, if not scroll to it
                    if bounding_box["y"] > page_size["height"]:
                        logger.info(f"Element is below viewport, scrolling to it")
                        await element.scroll_into_view_if_needed()
                        # Wait a bit for scroll to complete
                        await page.wait_for_timeout(500)
                        # Get updated bounding box after scroll
                        bounding_box = await element.bounding_box()
                        logger.info(f"Updated bounding box after scroll: {bounding_box}")

                    # Validate clip area is within reasonable bounds
                    if (bounding_box["width"] > 0 and bounding_box["height"] > 0 and
                        bounding_box["x"] >= 0 and bounding_box["y"] >= 0):
                        try:
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
                        except Exception as clip_error:
                            logger.warning(f"Clip screenshot failed: {clip_error}, trying element screenshot")
                            # Fallback to element screenshot
                            await element.screenshot(path=output_path)
                    else:
                        logger.warning(f"Invalid bounding box: {bounding_box}, taking element screenshot")
                        # Fallback to element screenshot
                        await element.screenshot(path=output_path)
                else:
                    logger.warning("Element found but no bounding box, taking full page screenshot")
                    # Fallback to full page screenshot
                    await page.screenshot(path=output_path)

            await browser.close()
            logger.info(f"Section screenshot saved at {output_path}")
            return True

    except Exception as e:
        logger.error(f"Failed to take section screenshot: {e}")
        return False
