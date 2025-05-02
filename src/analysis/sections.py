import logging
from agents import Agent, Runner

logger = logging.getLogger("agent-runner")

async def analyze_sections_side_by_side(mcp_server, base_url, preview_url):
    """Analyze the base URL to identify its sections structure."""
    try:
        logger.info(f"\n{'='*50}\n🔍 Starting base URL section analysis\n{'='*50}")

        # Identify sections in the base URL
        section_agent = Agent(
            name="Section Analyzer",
            instructions="""Analyze the base URL and identify all major sections.
            This will serve as our reference structure for visual comparison.

            For the base URL:
            1. List all major sections found
            2. Note their position and structure
            3. Describe the purpose of each section
            4. Note any important visual elements or patterns
            5. Note if the section animates or moves. This is important as it should probably be ignored.
            Format the response as:
            ### Base URL Structure:
            [Overall layout description]

            ### Sections (in order of appearance):
            1. [Section Name]
               - Position: [description]
               - Purpose: [description]
               - Key Elements: [list]
               - Visual Patterns: [description]
               - Animation : [description]

            2. [Section Name]
               ...

            This structural information will be used as a reference to analyze visual changes in the preview URL.""",
            mcp_servers=[mcp_server]
        )

        section_prompt = f"""Please analyze this base URL to establish our reference structure:
        Base URL: {base_url}

        Focus on identifying all major sections and their characteristics.
        This will serve as our baseline for comparing visual changes."""

        section_result = await Runner.run(section_agent, section_prompt)
        sections_analysis = section_result.final_output
        logger.info(f"\n{'='*50}\n🗺️ Base URL Section Analysis:\n{sections_analysis}\n{'='*50}")

        return sections_analysis

    except Exception as e:
        logger.error(f"Error during section analysis: {e}")
        raise
