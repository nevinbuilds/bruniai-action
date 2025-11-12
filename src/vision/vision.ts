import { Stagehand } from "@browserbasehq/stagehand";
import {
  escapeCurlyBraces,
  validateAndFixEnums,
  generateMetadata,
} from "./utils.js";
import {
  VisualAnalysisResultSchema,
  type VisualAnalysisResult,
} from "./types.js";

/**
 * Analyze screenshots using Stagehand agent to identify visual differences.
 *
 * This function replicates the Python analyze_images_with_vision functionality
 * using Stagehand's extract() method with structured output.
 *
 * @param base_screenshot - Path to the base screenshot
 * @param pr_screenshot - Path to the PR screenshot
 * @param diff_image - Path to the diff image (currently unused but kept for compatibility)
 * @param base_url - Base URL being tested
 * @param preview_url - Preview URL for the PR
 * @param pr_number - PR number
 * @param repository - Repository name
 * @param sections_analysis - Optional analysis of website sections
 * @param pr_title - Optional PR title for context
 * @param pr_description - Optional PR description for context (will be truncated if too long)
 * @param user_id - Optional user ID
 * @returns Complete structured report data matching the ReportData format
 */
export async function analyzeImagesWithVision(
  _base_screenshot: string,
  _pr_screenshot: string,
  _diff_image: string,
  base_url: string,
  preview_url: string,
  pr_number: string,
  repository: string,
  sections_analysis?: string,
  pr_title?: string,
  pr_description?: string,
  user_id?: string
): Promise<VisualAnalysisResult> {
  console.log(
    `\n${"=".repeat(50)}\n🔍 Starting image-based analysis\n${"=".repeat(50)}`
  );

  try {
    // Format PR title and description with escaped curly braces
    const prTitleFormatted = escapeCurlyBraces(
      pr_title || "No title provided."
    );
    const truncatedDescFormatted = escapeCurlyBraces(
      pr_description
        ? pr_description.slice(0, 200) +
            (pr_description.length > 200 ? "..." : "")
        : "No description provided."
    );

    // Initialize Stagehand
    const stagehand = new Stagehand({
      env: "LOCAL",
      localBrowserLaunchOptions: {
        headless: true,
      },
    });

    await stagehand.init();
    const page = stagehand.context.pages()[0];

    // Navigate to base URL first to establish reference
    console.log(`Navigating to base URL: ${base_url}`);
    await page.goto(base_url, {
      waitUntil: "networkidle",
      timeoutMs: 60000,
    });

    // Navigate to preview URL for comparison
    console.log(`Navigating to preview URL: ${preview_url}`);
    await page.goto(preview_url, {
      waitUntil: "networkidle",
      timeoutMs: 60000,
    });

    // Build the system prompt (same as Python version)
    const systemPrompt = `
                    You are a system designed to identify structural and visual changes in websites for testing purposes. Your primary responsibility is to detect and report significant structural changes, with a particular focus on missing or altered sections.

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

                    4. Extract the relative URL for the current page being tested.
                       - The relative URL is the URL of the current page being tested. Remove the base URL from the preview_url.
                       - The resulting relative URL should be used to determine if the PR title and description refer to the current page being tested.
                       - The title is !!!${prTitleFormatted}!!! and the description is !!!${truncatedDescFormatted}!!!
                        - If its clear to what page the PR title and description are referring to and they refer to the current page being tested (preview_url), then use it as user intent. Otherwise don't take them in consideration.
                        - In the case its very clear that they refer to this page (relative url), then pay close attention to the PR title and description for mentions of theme, color adjustments, or statements indicating "nothing changes visually" for the page being tested.

                    Non-critical changes (Should be noted but not flagged as issues):
                    - Text content changes
                    - Menu item text updates
                    - Headline modifications
                    - Product information updates
                    - Price changes
                    - Minor styling changes that don't affect layout
                    - If the section animates or moves
                    - If the PR title and description refer to a page that is not the current page being tested, then don't take them in consideration.

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
                                    "description": "Description of the section and its expected location/content if missing",
                                    "section_id": "section_id_will_be_filled"
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
                    - recommendation_enum: "reject" for critical failures that break functionality, "review_required" for changes needing human review, "pass" for acceptable changes
                    - Be specific in descriptions and highlight the reasoning behind your assessment
                    - Focus on structural integrity and missing sections as the most critical issues
                    - Note animations as non-critical but important context

                    You are currently viewing the PREVIEW URL (PR version) at: ${preview_url}
                    The BASE URL (reference) is: ${base_url}

                    Analyze the current page (PR version) and compare it against what should be present based on the base URL structure.
                    ${
                      sections_analysis
                        ? `\n\nHere is the structural analysis of the website's sections that you should use to guide your visual analysis<<<:\n\n${sections_analysis}>>>.\n\n**For each section listed above, explicitly check if it is present in the current page (PR version). If any section is missing, list it by name and describe its expected location and content.**\nFocus the image diff analysis on the sections that are not animating.`
                        : ""
                    }
                `;

    // Use Stagehand extract() with structured output
    let analysisData: Partial<VisualAnalysisResult>;
    try {
      analysisData = await stagehand.extract(
        systemPrompt,
        VisualAnalysisResultSchema
      );
    } catch (error) {
      console.error("Error during Stagehand extract:", error);
      throw new Error(`Failed to extract visual analysis: ${error}`);
    } finally {
      await stagehand.close();
    }

    // Fill in the actual metadata values
    const metadata = generateMetadata();
    analysisData.id = metadata.id;
    analysisData.url = base_url;
    analysisData.preview_url = preview_url;
    analysisData.pr_number = pr_number;
    analysisData.repository = repository;
    analysisData.timestamp = metadata.timestamp;
    analysisData.created_at = metadata.created_at;
    analysisData.user_id = user_id;

    // Ensure status field matches status_enum for backward compatibility
    if (analysisData.status_enum) {
      analysisData.status = analysisData.status_enum;
    }

    // Validate and fix enum values
    const validatedData = validateAndFixEnums(analysisData);

    console.log(
      `\n${"=".repeat(
        50
      )}\n🎨 Visual Analysis Results (JSON):\n${JSON.stringify(
        validatedData,
        null,
        2
      )}\n${"=".repeat(50)}`
    );

    return validatedData;
  } catch (error) {
    console.error(`Error during image analysis: ${error}`);
    throw error;
  }
}
