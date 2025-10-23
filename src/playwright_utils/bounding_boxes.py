import logging
import re
from playwright.async_api import async_playwright

logger = logging.getLogger("agent-runner")

def parse_section_ids_from_analysis(sections_analysis):
    """Parse section IDs from the MCP analysis output.

    Args:
        sections_analysis: String output from the section analysis

    Returns:
        List of section IDs found in the analysis
    """
    section_ids = []
    if not sections_analysis:
        return section_ids

    # Look for "Section ID: [id]" pattern in the analysis
    pattern = r"Section ID:\s*([a-zA-Z0-9\-_]+)"
    matches = re.findall(pattern, sections_analysis)
    section_ids.extend(matches)

    logger.info(f"Parsed section IDs from analysis: {section_ids}")
    return section_ids

async def extract_section_bounding_boxes(url, selector="section,header,footer,main,nav,aside", sections_analysis=None):
    """Extract section bounding boxes and match them with section IDs from analysis.

    Args:
        url: URL to analyze
        selector: CSS selector for sections
        sections_analysis: Optional analysis output containing section IDs

    Returns:
        List of section data with bounding boxes and matched IDs
    """
    try:
        # Parse section IDs from analysis if provided
        section_ids = parse_section_ids_from_analysis(sections_analysis) if sections_analysis else []

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

                    // Try to find a matching section ID based on content or attributes
                    let sectionId = null;
                    const nodeText = node.textContent || '';
                    const nodeId = node.getAttribute('id') || '';
                    const nodeClass = node.getAttribute('class') || '';

                    return {
                        label,
                        tag: node.tagName,
                        boundingBox: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        textContent: nodeText.substring(0, 100), // First 100 chars for matching
                        id: nodeId,
                        className: nodeClass
                    };
                })"""
            )

            await browser.close()

            # Try to match sections with IDs from analysis
            enriched_sections = []
            for i, section in enumerate(sections):
                section_id = None

                # If we have section IDs from analysis, try to match them
                if section_ids and i < len(section_ids):
                    section_id = section_ids[i]
                else:
                    # Generate a fallback ID
                    section_id = f"section-{i}"

                section['section_id'] = section_id
                enriched_sections.append(section)

            logger.info(f"Extracted {len(enriched_sections)} sections with IDs")
            return enriched_sections

    except Exception as e:
        logger.error(f"Error extracting section bounding boxes: {e}")
        return []
