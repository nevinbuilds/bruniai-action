import logging
import base64
import openai
import json
import uuid
from datetime import datetime

logger = logging.getLogger("agent-runner")

async def analyze_images_with_vision(
    base_screenshot: str,
    pr_screenshot: str,
    diff_image: str,
    base_url: str,
    preview_url: str,
    pr_number: str,
    repository: str,
    sections_analysis: str = None,
    pr_title: str = None,
    pr_description: str = None,
    user_id: str = None
):
    """Analyze screenshots using GPT-4 Vision API to identify visual differences.

    Args:
        base_screenshot: Path to the base screenshot
        pr_screenshot: Path to the PR screenshot
        diff_image: Path to the diff image
        base_url: Base URL being tested
        preview_url: Preview URL for the PR
        pr_number: PR number
        sections_analysis: Optional analysis of website sections
        pr_title: Optional PR title for context
        pr_description: Optional PR description for context (will be truncated if too long)
        user_id: Optional user ID

    Returns:
        Dict: Complete structured report data matching the ReportData format
    """
    logger.info(f"\n{'='*50}\n🔍 Starting image-based analysis\n{'='*50}")

    try:
        # Encode images to base64
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        base64_base = encode_image(base_screenshot.replace('.png', '-resized.png'))
        base64_pr = encode_image(pr_screenshot.replace('.png', '-resized.png'))
        # base64_diff = encode_image(diff_image)

        # Create OpenAI client
        client = openai.OpenAI()

        # Add PR context if available
        if pr_title or pr_description:
            pr_context = []
            if pr_title:
                pr_context.append(f"PR Title: !!!{pr_title}!!!")
            if pr_description:
                # Truncate description to 200 characters
                truncated_desc = pr_description[:200] + ("..." if len(pr_description) > 200 else "")
                pr_context.append(f"PR Description: !!!{truncated_desc}!!!")

        # Prepare the messages for GPT-4 Vision
        messages = [
            {
                "role": "system",
                "content": """
                    You are a system designed to identify structural and visual changes in websites for testing purposes. Your primary responsibility is to detect and report significant structural changes, with a particular focus on missing or altered sections.
                    Always make sure you are using the PR title and description to guide your analysis and identify if a certain change is expected or not.

                    Critical checks (Must be performed first):
                    1. Section presence check:
                       - For each section described in the section analysis, **explicitly check if that section is visually present in the PR image**.
                       - **Iterate through the list of sections provided in the sections analysis one by one. For each, state whether it is present or missing in the PR image.**
                       - A missing section is a CRITICAL issue and should be reported as a missing section.
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
                       - If a section in the middle of the page is missing, that will affect all sections below it but we should only flag the one missing section and continue
                       with the analysis of the following sections independently.

                    3. Visual hierarchy check:
                       - Verify if the visual hierarchy of elements remains consistent
                       - Check if important UI elements maintain their relative positioning
                       - Ensure navigation elements remain accessible
                       - Use the sections analysis to guide your analysis, the analysis will be delimited by ###.

                    4. Visual diff analysis:
                       - Analyze the diff image to identify visual differences
                       - Identify if the visual differences are significant
                       - Identify if the visual differences are minor
                       - Identify if the visual differences are critical
                       - Make sure to take in consideration the PR title and description to guide your analysis, the analysis will be delimited by <<<>>>.
                       - Use the sections analysis to guide your analysis, the pr_title and pr_description will be delimited by !!!.
                       - If the visual differences are significant, that will affect all sections below it but we should only flag the one missing section and continue

                    Non-critical changes (Should be noted but not flagged as issues):
                    - Text content changes
                    - Menu item text updates
                    - Headline modifications
                    - Product information updates
                    - Price changes
                    - Minor styling changes that don't affect layout
                    - If the section animates or moves

                    Changes that require human review:
                    - Most color changes if significant (change of color)
                    - Most styling changes if significant
                    - Most layout changes if significant
                    - Anything that goes against the PR title and description implicit requirements

                    **IMPORTANT CONSIDERATIONS FROM PR CONTEXT:**
                    - Pay close attention to the PR title and description for explicit mentions of theme, color adjustments, or statements indicating "nothing changes visually".
                    - If the PR specifically states that no visual changes are expected (e.g., "nothing changes visually" or "backend-only changes"), this should be the gold rule for the visual analysis. Because this represents user intent.
                    - User intention expressed via the PR title and description should be the most important metric for the visual analysis.

                    **IMPORTANT: You must respond with valid JSON only, following this exact structure:**

                    {
                        "id": "auto-generated-uuid",
                        "url": "base_url_will_be_filled",
                        "preview_url": "preview_url_will_be_filled",
                        "repository": "repository_will_be_filled",
                        "pr_number": "pr_number_will_be_filled",
                        "timestamp": "timestamp_will_be_filled",
                        "status": "pass" | "fail" | "warning" | "none",
                        "status_enum": "pass" | "fail" | "warning" | "none",
                        "critical_issues": {
                            "sections": [
                                {
                                    "name": "Section Name",
                                    "status": "Present" | "Missing",
                                    "description": "Description of the section and its expected location/content if missing"
                                }
                                ...
                            ],
                            "summary": "Summary of all critical issues found"
                        },
                        "critical_issues_enum": "none" | "missing_sections" | "other_issues",
                        "structural_analysis": {
                            "section_order": "Analysis of section ordering changes",
                            "layout": "Analysis of layout structure changes",
                            "broken_layouts": "Description of any broken layouts found"
                        },
                        "visual_changes": {
                            "diff_highlights": ["List of specific visual differences found"],
                            "animation_issues": "Description of any animation-related findings",
                            "conclusion": "Overall conclusion about visual changes"
                        },
                        "visual_changes_enum": "none" | "minor" | "significant",
                        "conclusion": {
                            "critical_issues": "Summary of critical issues impact",
                            "visual_changes": "Summary of visual changes impact",
                            "recommendation": "pass" | "review_required" | "reject",
                            "summary": "Overall summary and reasoning for recommendation"
                        },
                        "recommendation_enum": "pass" | "review_required" | "reject",
                        "created_at": "timestamp_will_be_filled",
                        "user_id": "user_id_will_be_filled"
                    }

                    **CRITICAL: You MUST use ONLY these exact enum values - do not create new ones:**

                    - status_enum: MUST be one of: "pass", "fail", "warning", "none"
                    - critical_issues_enum: MUST be one of: "none", "missing_sections", "other_issues"
                    - visual_changes_enum: MUST be one of: "none", "minor", "significant"
                    - recommendation_enum: MUST be one of: "pass", "review_required", "reject"
                    - section status: MUST be one of: "Present", "Missing"

                    Guidelines for setting enum values:
                    - status_enum: "fail" for critical issues, "warning" for significant changes needing review, "pass" for acceptable changes, "none" only for errors
                    - critical_issues_enum: "missing_sections" if ANY sections are missing, "other_issues" for structural problems, "none" if no critical issues
                    - visual_changes_enum: "significant" for major layout/visual changes, "minor" for small styling changes, "none" for no meaningful changes
                    - recommendation_enum: "reject" for critical failures that break functionality, "review_required" for changes needing human review, "pass" for acceptable changes. if the PR's intention goes against the visual changes, then the recommendation should be "review_required" or "reject" depending on the severity of the changes.
                    - Be specific in descriptions and highlight the reasoning behind your assessment
                    - Focus on structural integrity and missing sections as the most critical issues
                    - Note animations as non-critical but important context
                    - Always prioritize the user's explicit intention as conveyed in the PR title and description when assessing visual differences. If the PR states that no visual changes are expected, treat any detected visual changes with a higher degree of scrutiny, potentially flagging them as critical if they contradict the stated intention.
                """
            }
        ]

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
                    "text": "Here are the images to analyze in the right order. Base Image, PR Image and Diff Image. Please respond with the JSON analysis following the exact structure specified in the system prompt."
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
                }
            ]
        })

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            max_tokens=1500,
            temperature=0.2  # Lower temperature for more consistent analysis
        )

        analysis_text = response.choices[0].message.content

        # Parse the JSON response
        try:
            analysis_data = json.loads(analysis_text)

            # Fill in the actual metadata values
            analysis_data["id"] = str(uuid.uuid4())
            analysis_data["url"] = base_url
            analysis_data["preview_url"] = preview_url
            analysis_data["pr_number"] = pr_number
            analysis_data["repository"] = repository
            analysis_data["timestamp"] = datetime.utcnow().isoformat()
            analysis_data["created_at"] = datetime.utcnow().isoformat()
            analysis_data["user_id"] = user_id

            # Ensure status field matches status_enum for backward compatibility
            if "status_enum" in analysis_data:
                analysis_data["status"] = analysis_data["status_enum"]

            # Validate enum values and provide fallbacks for invalid ones
            valid_status_enum = ['pass', 'fail', 'warning', 'none']
            valid_critical_issues_enum = ['none', 'missing_sections', 'other_issues']
            valid_visual_changes_enum = ['none', 'minor', 'significant']
            valid_recommendation_enum = ['pass', 'review_required', 'reject']

            # Validate and correct enum values
            if analysis_data.get('status_enum') not in valid_status_enum:
                logger.warning(f"Invalid status_enum: {analysis_data.get('status_enum')}, defaulting to 'warning'")
                analysis_data['status_enum'] = 'warning'
                analysis_data['status'] = 'warning'

            if analysis_data.get('critical_issues_enum') not in valid_critical_issues_enum:
                logger.warning(f"Invalid critical_issues_enum: {analysis_data.get('critical_issues_enum')}, defaulting to 'other_issues'")
                analysis_data['critical_issues_enum'] = 'other_issues'

            if analysis_data.get('visual_changes_enum') not in valid_visual_changes_enum:
                logger.warning(f"Invalid visual_changes_enum: {analysis_data.get('visual_changes_enum')}, defaulting to 'minor'")
                analysis_data['visual_changes_enum'] = 'minor'

            if analysis_data.get('recommendation_enum') not in valid_recommendation_enum:
                logger.warning(f"Invalid recommendation_enum: {analysis_data.get('recommendation_enum')}, defaulting to 'review_required'")
                analysis_data['recommendation_enum'] = 'review_required'

            # Validate section status values
            critical_issues = analysis_data.get('critical_issues', {})
            sections = critical_issues.get('sections', [])
            for section in sections:
                if section.get('status') not in ['Present', 'Missing']:
                    logger.warning(f"Invalid section status: {section.get('status')}, defaulting to 'Present'")
                    section['status'] = 'Present'

            logger.info(f"\n{'='*50}\n🎨 Visual Analysis Results (JSON):\n{json.dumps(analysis_data, indent=2)}\n{'='*50}")
            return analysis_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {analysis_text}")
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")

    except Exception as e:
        logger.error(f"Error during image analysis: {e}")
        raise
