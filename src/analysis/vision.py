import logging
import base64
import openai

logger = logging.getLogger("agent-runner")

async def analyze_images_with_vision(base_screenshot: str, pr_screenshot: str, diff_image: str, sections_analysis: str = None, pr_title: str = None, pr_description: str = None):
    """Analyze screenshots using GPT-4 Vision API to identify visual differences.

    Args:
        base_screenshot: Path to the base screenshot
        pr_screenshot: Path to the PR screenshot
        diff_image: Path to the diff image
        sections_analysis: Optional analysis of website sections
        pr_title: Optional PR title for context
        pr_description: Optional PR description for context (will be truncated if too long)
    """
    logger.info(f"\n{'='*50}\n🔍 Starting image-based analysis\n{'='*50}")

    try:
        # Encode images to base64
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        base64_base = encode_image(base_screenshot.replace('.png', '-resized.png'))
        base64_pr = encode_image(pr_screenshot.replace('.png', '-resized.png'))
        base64_diff = encode_image(diff_image)

        # Create OpenAI client
        client = openai.OpenAI()

        # Prepare the messages for GPT-4 Vision
        messages = [
            {
                "role": "system",
                "content": """
                    You are a system designed to identify structural and visual changes in websites for testing purposes. Your primary responsibility is to detect and report significant structural changes, with a particular focus on missing or altered sections.

                    Critical checks (Must be performed first):
                    1. Section presence check:
                       - For each section described in the section analysis, **explicitly check if that section is visually present in the PR image**.
                       - **Iterate through the list of sections one by one. For each, state whether it is present or missing in the PR image.**
                       - A missing section is a CRITICAL issue and should be reported prominently.
                       - This check must be performed before any other analysis.
                       - If a section exists in the base image and section analysis but not in the PR image, this is a critical failure.
                       - Use the sections analysis to guide your decisions, the analysis will be delimited by <<<>>>.
                       - If the section animates or moves make sure to point it out and take in consideration to not flag as visual regression on things that are animating.

                    2. Structural changes check:
                       - Identify if sections have moved positions
                       - Check if the overall layout structure has changed
                       - Verify if major UI components have been relocated
                       - These are considered significant issues
                       - Use the sections analysis to guide your analysis, the analysis will be delimited by ###.

                    3. Visual hierarchy check:
                       - Verify if the visual hierarchy of elements remains consistent
                       - Check if important UI elements maintain their relative positioning
                       - Ensure navigation elements remain accessible
                       - Use the sections analysis to guide your analysis, the analysis will be delimited by ###.

                    Non-critical changes (Should be noted but not flagged as issues):
                    - Text content changes
                    - Menu item text updates
                    - Headline modifications
                    - Product information updates
                    - Price changes
                    - Minor styling changes that don't affect layout
                    - If the section animates or moves

                    Format your response as follows:
                    <details>
                    <summary>Critical issues</summary>

                    For each section in the analysis, state:
                       - Section Name: [Present/Missing]
                       - If missing, describe its expected location and content.
                       - List any major structural changes
                       - List any broken layouts
                    </details>

                    <details>
                    <summary>Structural analysis</summary>

                    Compare each section's presence and position
                       - Note any layout modifications
                    </details>

                    <details>
                    <summary>Visual changes</summary>

                    Document non-critical changes
                       - Note any styling updates
                       - If a section is animating or moving, report that it is animating or moving as that can be the cause of a diff in a section.
                    </details>

                    Conclusion:
                       - When passing use an alert of type [!TIP] for github and when recommending a review use an alert of type [!WARNING] (see information below for the format)
                       - Clearly state if there are any critical issues
                       - Even if there are not critical issues, always describe where any visual changes are and why they are not critical.
                       - Provide a pass/review recommendation

                    Example of the alert format:
                    > [!TIP]
                    > This is a tip alert
                """
            }
        ]

        # Add PR context if available
        if pr_title or pr_description:
            pr_context = []
            if pr_title:
                pr_context.append(f"PR Title: {pr_title}")
            if pr_description:
                # Truncate description to 200 characters
                truncated_desc = pr_description[:200] + ("..." if len(pr_description) > 200 else "")
                pr_context.append(f"PR Description: {truncated_desc}")

            messages.append({
                "role": "user",
                "content": f"Here is the context about this PR:\n\n{' '.join(pr_context)}\n\nUse this information to better understand the expected changes in the screenshots."
            })

        if sections_analysis:
            messages.append({
                "role": "user",
                "content": (
                    f"Here is the structural analysis of the website's sections that you should use to guide your visual analysis<<<:\n\n{sections_analysis}>>>.\n\n"
                    "**For each section listed above, explicitly check if it is present in the PR screenshot. If any section is missing, list it by name and describe its expected location and content.**"
                    "Focus the image diff analysis on the sections that are not animating."
                )
            })

        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here are the images to analyze in the right order. Base Image, PR Image and Diff Image."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_base}"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_pr}"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_diff}"
                    }
                }
            ]
        })

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            max_tokens=1000,
            temperature=0.2  # Lower temperature for more consistent analysis
        )

        analysis = response.choices[0].message.content
        logger.info(f"\n{'='*50}\n🎨 Visual Analysis Results:\n{analysis}\n{'='*50}")
        return analysis

    except Exception as e:
        logger.error(f"Error during image analysis: {e}")
        return f"Error performing image analysis: {str(e)}"
