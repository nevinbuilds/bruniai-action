import logging
import asyncio
from agents import Agent, Runner
from agents.exceptions import AgentsException
from playwright.async_api import async_playwright

logger = logging.getLogger("agent-runner")

async def extract_real_dom_info(url):
    """Extract real DOM information using Playwright directly to avoid MCP server limitations."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Extract real DOM information
            dom_info = await page.eval_on_selector_all(
                "section,header,footer,main,nav,aside,article,div[class*='section'],div[class*='hero'],div[class*='content'],div[class*='container']",
                """(nodes) => nodes.map((node, idx) => {
                    const rect = node.getBoundingClientRect();

                    // Skip elements that are too small or not visible
                    if (rect.width < 50 || rect.height < 50) {
                        return null;
                    }

                    const nodeId = node.getAttribute('id') || '';
                    const nodeClass = node.getAttribute('class') || '';
                    const ariaLabel = node.getAttribute('aria-label') || '';
                    const tagName = node.tagName.toLowerCase();
                    const textContent = (node.textContent || '').substring(0, 100);

                    return {
                        tag: tagName,
                        id: nodeId,
                        className: nodeClass,
                        ariaLabel: ariaLabel,
                        textContent: textContent,
                        boundingBox: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    };
                }).filter(node => node !== null)"""
            )

            await browser.close()
            return dom_info

    except Exception as e:
        logger.error(f"Error extracting DOM info: {e}")
        return []

async def analyze_sections_side_by_side(mcp_server, base_url, preview_url):
    """Analyze the base URL to identify its sections structure."""
    max_retries = 3
    retry_delay = 15  # seconds

    for attempt in range(max_retries):
        try:
            logger.info(f"\n{'='*50}\n🔍 Starting base URL section analysis (attempt {attempt + 1}/{max_retries})\n{'='*50}")

            # Extract real DOM information first
            logger.info("Extracting real DOM information using Playwright...")
            dom_info = await extract_real_dom_info(base_url)
            logger.info(f"Found {len(dom_info)} DOM elements with real class names")

            # Create a summary of the real DOM structure for the agent
            dom_summary = "Real DOM Structure:\n"
            for i, element in enumerate(dom_info):
                dom_summary += f"{i+1}. {element['tag'].upper()} element:\n"
                dom_summary += f"   - ID: {element['id'] or 'none'}\n"
                dom_summary += f"   - Classes: {element['className'] or 'none'}\n"
                dom_summary += f"   - ARIA Label: {element['ariaLabel'] or 'none'}\n"
                dom_summary += f"   - Content: {element['textContent'][:50]}...\n"
                dom_summary += f"   - Position: {element['boundingBox']['x']}, {element['boundingBox']['y']}\n\n"

            # Identify sections in the base URL
            section_agent = Agent(
                name="Section Analyzer",
                instructions="""Analyze the base URL and identify all major sections.
                This will serve as our reference structure for visual comparison.

                For the base URL:
                1. List all major sections found. Make sure that the sections actually exist in the base URL and has some content (is not empty), they should be well visible, have content and has actual key elements in it.
                2. Note their position and structure
                3. Describe the purpose of each section
                4. Note any important visual elements or patterns
                5. Note if the section animates or moves. This is important as it should probably be ignored.
                6. Generate a unique, descriptive ID for each section (e.g., "hero-section", "features-section", "footer-section")
                7. **CRITICAL**: For each section, identify the HTML element that represents it. Use the provided real DOM structure information to get accurate attributes:
                   - HTML tag names (section, div, header, footer, main, nav, aside, article)
                   - ID attributes (e.g., id="hero", id="navigation") - use "none" if no ID
                   - Class names - Use the REAL class names from the DOM structure provided below. Do not guess or assume.
                   - Data attributes (e.g., data-section="hero")
                   - ARIA labels or roles
                   - Make sure to decide on the element that best represents the start of the section (and will end at the beginning of the next section)

                   **IMPORTANT**: Use the real DOM structure information provided in the prompt to get accurate class names and attributes. The DOM structure below contains the actual extracted information from the page.

                Format the response as:
                ### Base URL Structure:
                [Overall layout description]

                ### Sections (in order of appearance):
                1. [Section Name]
                   - Section ID: [unique-descriptive-id]
                   - Position: [description]
                   - Purpose: [description]
                   - Key Elements: [list]
                   - Visual Patterns: [description]
                   - Animation: [description]
                   - HTML Element: [tag name, e.g., "section", "div", "header"]
                   - HTML ID: [id attribute if present, or "none"]
                   - HTML Classes: [class names if present, or "none"]
                   - ARIA Label: [aria-label if present, or "none"]
                   - Content Identifier: [first few words of content for matching]

                2. [Section Name]
                   - Section ID: [unique-descriptive-id]
                   ...

                This structural information will be used as a reference to analyze visual changes in the preview URL.""",
                mcp_servers=[mcp_server]
            )

            section_prompt = f"""Please analyze this base URL to establish our reference structure:
            Base URL: {base_url}

            Focus on identifying all major sections and their characteristics. Make sure that the sections actually exist in the base URL,
            they should be well visible and only list the ones that are actually present. Don't register sections that are not present in the base URL.

            **CRITICAL**: Use the real DOM structure information provided below to get accurate class names and attributes. This information was extracted directly from the page using Playwright and contains the actual class names, IDs, and other attributes.

            {dom_summary}

            This will serve as our baseline for comparing visual changes."""

            # Add timeout to the Runner.run call
            try:
                section_result = await asyncio.wait_for(
                    Runner.run(section_agent, section_prompt),
                    timeout=120  # 2 minutes timeout
                )
                sections_analysis = section_result.final_output
                logger.info(f"\n{'='*50}\n🗺️ Base URL Section Analysis:\n{sections_analysis}\n{'='*50}")
                return sections_analysis

            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    logger.warning(f"Section analysis timed out. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise Exception("Section analysis timed out after all retries")

        except AgentsException as e:
            if "browser_navigate" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Browser navigation failed. Retrying in {retry_delay} seconds... Error: {e}")
                await asyncio.sleep(retry_delay)
                continue
            else:
                logger.error(f"Error during section analysis: {e}")
                raise

        except Exception as e:
            logger.error(f"Error during section analysis: {e}")
            if attempt < max_retries - 1:
                logger.warning(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            raise
