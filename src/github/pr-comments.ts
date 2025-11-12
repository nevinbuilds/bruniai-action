/**
 * GitHub PR comment utilities.
 * Functions for extracting PR numbers from GitHub event files,
 * formatting visual analysis results, and posting PR comments.
 */

import { readFile } from "fs/promises";
import type { VisualAnalysisResult } from "../vision/types.js";
import { getGithubAppToken } from "./auth.js";

/**
 * GitHub event payload structure.
 */
interface GitHubEvent {
  pull_request?: {
    number: number;
  };
  issue?: {
    number: number;
  };
}

/**
 * Extract PR number from GitHub event file.
 * Equivalent to Python's get_pr_number_from_event().
 *
 * Reads the GitHub event JSON file and extracts the PR number
 * from either pull_request.number or issue.number.
 *
 * @returns PR number, or null if not found or error occurs
 */
export async function getPrNumberFromEvent(): Promise<number | null> {
  const eventPath = process.env.GITHUB_EVENT_PATH;
  const repository = process.env.GITHUB_REPOSITORY;

  if (!eventPath || !repository) {
    console.warn("GITHUB_EVENT_PATH not found or GITHUB_REPOSITORY not set.");
    return null;
  }

  try {
    const eventContent = await readFile(eventPath, "utf-8");
    const event: GitHubEvent = JSON.parse(eventContent);

    const prNumber = event.pull_request?.number || event.issue?.number || null;

    if (!prNumber) {
      console.warn("PR number not found in event payload.");
    }
    return prNumber;
  } catch (error) {
    console.error("Error reading PR number from event:", error);
    return null;
  }
}

/**
 * Determine status and emoji from visual analysis data.
 * Equivalent to Python's determine_status_from_visual_analysis().
 *
 * @param visualAnalysis - Visual analysis result object or string
 * @returns Tuple of [status, emoji] where status is 'pass', 'warning', 'fail', or 'none'
 */
export function determineStatusFromVisualAnalysis(
  visualAnalysis: VisualAnalysisResult | string | null | undefined
): [string, string] {
  if (!visualAnalysis) {
    return ["none", "❓"];
  }

  // Handle string-based analysis (fallback)
  if (typeof visualAnalysis === "string") {
    const analysisText = visualAnalysis.toLowerCase();
    let status: string;
    if (
      analysisText.includes("missing sections") ||
      analysisText.includes("critical")
    ) {
      status = "fail";
    } else if (
      (analysisText.includes("significant changes") &&
        !analysisText.includes("no significant changes")) ||
      analysisText.includes("review required")
    ) {
      status = "warning";
    } else {
      status = "pass";
    }

    const statusEmoji: Record<string, string> = {
      pass: "✅",
      warning: "⚠️",
      fail: "❌",
      none: "❓",
    };

    return [status, statusEmoji[status] || "❓"];
  }

  // Handle structured VisualAnalysisResult object
  let status = "pass"; // Default to pass

  // Check for critical issues first
  const criticalIssuesEnum = visualAnalysis.critical_issues_enum || "none";
  if (criticalIssuesEnum !== "none") {
    status = "fail";
  } else {
    // Check for visual changes
    const visualChangesEnum = visualAnalysis.visual_changes_enum || "none";
    const recommendationEnum = visualAnalysis.recommendation_enum || "pass";

    if (
      visualChangesEnum === "significant" ||
      recommendationEnum === "review_required"
    ) {
      status = "warning";
    } else if (visualChangesEnum === "minor") {
      status = "warning";
    } else {
      status = "pass";
    }
  }

  // Map status to emoji
  const statusEmoji: Record<string, string> = {
    pass: "✅",
    warning: "⚠️",
    fail: "❌",
    none: "❓",
  };

  return [status, statusEmoji[status] || "❓"];
}

/**
 * Determine overall test status from multiple reports.
 * Equivalent to Python's get_test_status().
 *
 * Logic:
 * - If any report has status 'fail' -> overall status is 'fail'
 * - Else if any report has status 'warning' -> overall status is 'warning'
 * - Else if any report has status 'pass' -> overall status is 'pass'
 * - If no reports or all are 'none' -> overall status is 'none'
 *
 * @param reports - Array of visual analysis result objects
 * @returns Overall status as string: 'pass', 'fail', 'warning', or 'none'
 */
export function getTestStatus(
  reports: VisualAnalysisResult[]
): "pass" | "fail" | "warning" | "none" {
  if (!reports || reports.length === 0) {
    return "none";
  }

  // Check for any failures first (highest priority)
  for (const report of reports) {
    const status = report.status || report.status_enum || "none";
    if (status === "fail") {
      return "fail";
    }
  }

  // Check for any warnings (second priority)
  for (const report of reports) {
    const status = report.status || report.status_enum || "none";
    if (status === "warning") {
      return "warning";
    }
  }

  // Check for any passes (third priority)
  for (const report of reports) {
    const status = report.status || report.status_enum || "none";
    if (status === "pass") {
      return "pass";
    }
  }

  // Default to none if no meaningful status found
  return "none";
}

/**
 * Convert structured visual analysis JSON to readable markdown format.
 * Equivalent to Python's format_visual_analysis_to_markdown().
 *
 * @param visualAnalysis - Visual analysis result object
 * @param reportUrl - Optional URL to the full report
 * @returns Formatted markdown string
 */
export function formatVisualAnalysisToMarkdown(
  visualAnalysis: VisualAnalysisResult | null | undefined,
  reportUrl?: string
): string {
  if (!visualAnalysis || typeof visualAnalysis !== "object") {
    return "❌ **Error**: No visual analysis data available";
  }

  const markdownParts: string[] = [];

  // Determine status using the general function
  const [status, statusEmoji] =
    determineStatusFromVisualAnalysis(visualAnalysis);

  // New format header
  const statusTitle = status
    .replace(/_/g, " ")
    .replace(/\b\w/g, (l) => l.toUpperCase());
  markdownParts.push(
    `## ${statusEmoji} Visual Testing Report — ${statusTitle}`
  );
  markdownParts.push(
    "*1 page analyzed by [bruniai](https://www.brunivisual.com/)*  "
  );

  // Add visual changes conclusion if available
  const visualChanges = visualAnalysis.visual_changes;
  const conclusion = visualChanges?.conclusion || "";
  if (conclusion) {
    markdownParts.push(`**Visual Changes:** ${statusEmoji} ${conclusion}`);
    markdownParts.push("");
  }

  // Add report URL if provided
  if (reportUrl) {
    markdownParts.push(`[📦 View Artifacts](${reportUrl})`);
  }

  markdownParts.push("");
  markdownParts.push("---");
  markdownParts.push("");

  // Critical Sections Check
  const criticalIssues = visualAnalysis.critical_issues;
  if (
    criticalIssues &&
    (criticalIssues.sections?.length > 0 || criticalIssues.summary)
  ) {
    markdownParts.push("### 🚨 Critical Sections Check");
    markdownParts.push("| Section | Status |");
    markdownParts.push("|----------------------------------------|--------|");

    const sections = criticalIssues.sections || [];
    if (sections.length > 0) {
      for (const section of sections) {
        const name = section.name || "Unknown Section";
        const sectionStatus = section.status || "Unknown";
        const statusIcon = sectionStatus === "Missing" ? "❌" : "✅";
        // Pad name to 38 characters for alignment (matching Python format)
        const paddedName = name.padEnd(38);
        markdownParts.push(`| ${paddedName} | ${statusIcon} |`);
      }
    }

    markdownParts.push("");
  }

  // Visual Changes
  if (visualChanges) {
    const hasVisualChanges =
      (visualChanges.diff_highlights?.length ?? 0) > 0 ||
      visualChanges.animation_issues ||
      visualChanges.conclusion;

    if (hasVisualChanges) {
      markdownParts.push("### 🎨 Visual Changes");

      const diffHighlights = visualChanges.diff_highlights || [];
      if (diffHighlights.length > 0) {
        for (const highlight of diffHighlights) {
          markdownParts.push(`- ${highlight}`);
        }
      }

      const animationIssues = visualChanges.animation_issues || "";
      if (animationIssues) {
        markdownParts.push(`- ${animationIssues}`);
      }

      const visualConclusion = visualChanges.conclusion || "";
      if (visualConclusion) {
        markdownParts.push(`- ${visualConclusion}`);
      }
      markdownParts.push("");
    }
  }

  // Structure
  const structural = visualAnalysis.structural_analysis;
  if (structural) {
    const hasStructural =
      structural.section_order ||
      structural.layout ||
      structural.broken_layouts;

    if (hasStructural) {
      markdownParts.push("### 🏗️ Structure");

      const sectionOrder = structural.section_order || "";
      if (sectionOrder) {
        markdownParts.push(`- Section order ${sectionOrder}`);
      }

      const layout = structural.layout || "";
      if (layout) {
        markdownParts.push(`- Layout ${layout}`);
      }

      const brokenLayouts = structural.broken_layouts || "";
      if (brokenLayouts) {
        markdownParts.push(`- ${brokenLayouts}`);
      }
      markdownParts.push("");

      // Reference Structure (collapsible section)
      markdownParts.push("<details>");
      markdownParts.push(
        "<summary>📖 Reference Structure (click to expand)</summary>"
      );
      markdownParts.push("");
      markdownParts.push("*(Your detailed analysis goes here)*");
      markdownParts.push("");
      markdownParts.push("</details>");
    }
  }

  return markdownParts.join("\n");
}

/**
 * Post or update a PR comment on GitHub.
 * Equivalent to Python's post_pr_comment().
 *
 * @param summary - The markdown summary to post
 */
export async function postPrComment(summary: string): Promise<void> {
  // Get GitHub App token
  const githubToken = getGithubAppToken();
  if (!githubToken) {
    console.error("Failed to get GitHub App token");
    return;
  }

  const repo = process.env.GITHUB_REPOSITORY; // e.g. 'org/repo'
  const prNumberEnv = process.env.PR_NUMBER;
  const runId = process.env.GITHUB_RUN_ID;

  console.log(`GITHUB_REPOSITORY: ${repo}`);
  console.log(`PR_NUMBER: ${prNumberEnv}`);
  console.log(`GITHUB_RUN_ID: ${runId}`);

  let prNumber: number | null = null;
  if (prNumberEnv) {
    const parsed = parseInt(prNumberEnv, 10);
    prNumber = isNaN(parsed) ? null : parsed;
  } else {
    prNumber = await getPrNumberFromEvent();
  }

  if (!githubToken || !repo || !prNumber) {
    console.warn("Missing GitHub context, skipping PR comment.");
    return;
  }

  // Add artifact links to the summary
  let finalSummary = summary;
  if (runId) {
    const artifactsUrl = `https://github.com/${repo}/actions/runs/${runId}`;
    finalSummary = `${summary}\n\n📦 [View Artifacts](${artifactsUrl}) for more details including screenshots.`;
  }

  // Prepare headers
  const headers = {
    Authorization: `token ${githubToken}`,
    Accept: "application/vnd.github.v3+json",
    "Content-Type": "application/json",
  };

  // Get all comments for the PR
  const commentsUrl = `https://api.github.com/repos/${repo}/issues/${prNumber}/comments`;
  let response: Response;

  try {
    response = await fetch(commentsUrl, { headers });
  } catch (error) {
    console.error(`Failed to fetch comments: ${error}`);
    return;
  }

  if (response.status !== 200) {
    const errorText = await response.text();
    console.error(`Failed to fetch comments: ${errorText}`);
    return;
  }

  const comments = (await response.json()) as Array<{
    id: number;
    body: string;
  }>;
  let existingCommentId: number | null = null;

  // Look for a comment that starts with our header
  for (const comment of comments) {
    const body = comment.body;
    if (
      body.startsWith(
        "Information about visual testing analysis provided by [bruniai]"
      ) ||
      body.startsWith("# ✅ Visual Testing Report") ||
      body.startsWith("# ⚠️ Visual Testing Report") ||
      body.startsWith("# ❌ Visual Testing Report")
    ) {
      existingCommentId = comment.id;
      break;
    }
  }

  if (existingCommentId) {
    // Update existing comment
    const updateUrl = `https://api.github.com/repos/${repo}/issues/comments/${existingCommentId}`;
    try {
      response = await fetch(updateUrl, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ body: finalSummary }),
      });

      if (response.status === 200) {
        console.log("📝 Successfully updated existing PR comment.");
      } else {
        const errorText = await response.text();
        console.error(`❌ Failed to update PR comment: ${errorText}`);
      }
    } catch (error) {
      console.error(`❌ Failed to update PR comment: ${error}`);
    }
  } else {
    // Create new comment
    try {
      response = await fetch(commentsUrl, {
        method: "POST",
        headers,
        body: JSON.stringify({ body: finalSummary }),
      });

      if (response.status === 201) {
        console.log("📝 Successfully created new PR comment.");
      } else {
        const errorText = await response.text();
        console.error(`❌ Failed to create PR comment: ${errorText}`);
      }
    } catch (error) {
      console.error(`❌ Failed to create PR comment: ${error}`);
    }
  }
}
