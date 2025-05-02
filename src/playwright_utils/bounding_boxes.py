import logging
from playwright.async_api import async_playwright

logger = logging.getLogger("agent-runner")

async def extract_section_bounding_boxes(url, selector="section,header,footer,main,nav,aside"):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Evaluate JS in the page to get bounding boxes
            sections = await page.eval_on_selector_all(
                selector,
                """(nodes) => nodes.map((node, idx) => {
                    const rect = node.getBoundingClientRect();
                    let label = node.getAttribute('aria-label') ||
                                node.getAttribute('id') ||
                                node.getAttribute('class') ||
                                node.tagName + '-' + idx;
                    return {
                        label,
                        tag: node.tagName,
                        boundingBox: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    };
                })"""
            )

            await browser.close()
            return sections
    except Exception as e:
        logger.error(f"Error extracting section bounding boxes: {e}")
        return []
