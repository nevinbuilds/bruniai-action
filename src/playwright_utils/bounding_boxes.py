import logging
import re
from playwright.async_api import async_playwright

logger = logging.getLogger("agent-runner")

def parse_section_data_from_analysis(sections_analysis):
    """Parse section data from the MCP analysis output.

    Args:
        sections_analysis: String output from the section analysis

    Returns:
        List of dictionaries containing section data
    """
    sections_data = []
    if not sections_analysis:
        return sections_data

    # Look for section blocks in the analysis
    section_pattern = r'(\d+)\.\s*([^\n]+)\s*\n(.*?)(?=\d+\.|$)'
    matches = re.findall(section_pattern, sections_analysis, re.DOTALL)

    for match in matches:
        section_num, section_name, section_content = match

        # Extract various attributes
        section_id_match = re.search(r'Section ID:\s*([a-zA-Z0-9\-_]+)', section_content)
        html_element_match = re.search(r'HTML Element:\s*([^\n]+)', section_content)
        html_id_match = re.search(r'HTML ID:\s*([^\n]+)', section_content)
        html_classes_match = re.search(r'HTML Classes:\s*([^\n]+)', section_content)
        aria_label_match = re.search(r'ARIA Label:\s*([^\n]+)', section_content)
        content_identifier_match = re.search(r'Content Identifier:\s*([^\n]+)', section_content)

        section_data = {
            'name': section_name.strip(),
            'section_id': section_id_match.group(1) if section_id_match else f"section-{section_num}",
            'html_element': html_element_match.group(1).strip() if html_element_match else None,
            'html_id': html_id_match.group(1).strip() if html_id_match else None,
            'html_classes': html_classes_match.group(1).strip() if html_classes_match else None,
            'aria_label': aria_label_match.group(1).strip() if aria_label_match else None,
            'content_identifier': content_identifier_match.group(1).strip() if content_identifier_match else None
        }

        # Clean up "none" values
        for key in ['html_id', 'html_classes', 'aria_label']:
            if section_data[key] and section_data[key].lower() == 'none':
                section_data[key] = None

        sections_data.append(section_data)

    logger.info(f"Parsed {len(sections_data)} sections from analysis")
    return sections_data

async def extract_section_bounding_boxes(url, selector="section,header,footer,main,nav,aside,article,div[class*='section'],div[class*='hero'],div[class*='content'],div[class*='container']", sections_analysis=None):
    """Extract section bounding boxes and match them with section data from analysis.

    Args:
        url: URL to analyze
        selector: CSS selector for sections
        sections_analysis: Optional analysis output containing section data

    Returns:
        List of section data with bounding boxes and matched IDs
    """
    try:
        # Parse section data from analysis if provided
        sections_data = parse_section_data_from_analysis(sections_analysis) if sections_analysis else []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Evaluate JS in the page to get bounding boxes with enhanced data
            sections = await page.eval_on_selector_all(
                selector,
                """(nodes) => nodes.map((node, idx) => {
                    const rect = node.getBoundingClientRect();

                    // Skip elements that are too small or not visible
                    if (rect.width < 50 || rect.height < 50) {
                        return null;
                    }

                    let label = node.getAttribute('aria-label') ||
                                node.getAttribute('id') ||
                                node.getAttribute('class') ||
                                node.tagName + '-' + idx;

                    const nodeText = node.textContent || '';
                    const nodeId = node.getAttribute('id') || '';
                    const nodeClass = node.getAttribute('class') || '';
                    const ariaLabel = node.getAttribute('aria-label') || '';
                    const dataAttributes = {};

                    // Extract data attributes
                    for (let attr of node.attributes) {
                        if (attr.name.startsWith('data-')) {
                            dataAttributes[attr.name] = attr.value;
                        }
                    }

                    return {
                        label,
                        tag: node.tagName.toLowerCase(),
                        boundingBox: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        textContent: nodeText.substring(0, 200), // First 200 chars for matching
                        id: nodeId,
                        className: nodeClass,
                        ariaLabel: ariaLabel,
                        dataAttributes: dataAttributes,
                        isVisible: rect.width > 0 && rect.height > 0
                    };
                }).filter(node => node !== null)"""
            )

            await browser.close()

            # Try to match sections with data from analysis
            enriched_sections = []
            for i, section in enumerate(sections):
                section_id = f"section-{i}"  # Default fallback
                matched_analysis = None

                # Try to match with analysis data
                if sections_data:
                    for analysis_section in sections_data:
                        if _match_section_to_analysis(section, analysis_section):
                            section_id = analysis_section['section_id']
                            matched_analysis = analysis_section
                            break

                section['section_id'] = section_id
                section['matched_analysis'] = matched_analysis
                enriched_sections.append(section)

            logger.info(f"Extracted {len(enriched_sections)} sections with IDs")
            return enriched_sections

    except Exception as e:
        logger.error(f"Error extracting section bounding boxes: {e}")
        return []

def _match_section_to_analysis(section, analysis_section):
    """Match a DOM section to analysis section data.

    Args:
        section: DOM section data
        analysis_section: Analysis section data

    Returns:
        bool: True if sections match
    """
    # Match by HTML ID
    if analysis_section.get('html_id') and section.get('id'):
        if analysis_section['html_id'].lower() == section['id'].lower():
            return True

    # Match by HTML classes
    if analysis_section.get('html_classes') and section.get('className'):
        analysis_classes = set(analysis_section['html_classes'].lower().split())
        section_classes = set(section['className'].lower().split())
        if analysis_classes.intersection(section_classes):
            return True

    # Match by ARIA label
    if analysis_section.get('aria_label') and section.get('ariaLabel'):
        if analysis_section['aria_label'].lower() == section['ariaLabel'].lower():
            return True

    # Match by content identifier
    if analysis_section.get('content_identifier') and section.get('textContent'):
        content_words = analysis_section['content_identifier'].lower().split()
        section_text = section['textContent'].lower()
        if all(word in section_text for word in content_words):
            return True

    # Match by tag name
    if analysis_section.get('html_element') and section.get('tag'):
        if analysis_section['html_element'].lower() == section['tag'].lower():
            return True

    return False
