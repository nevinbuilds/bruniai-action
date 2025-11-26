import { v4 as uuidv4 } from "uuid";
import type { VisualAnalysisResult } from "./types.js";

/**
 * Maximum length for PR title input.
 */
export const MAX_TITLE_LENGTH = 200;

/**
 * Maximum length for PR description input.
 */
export const MAX_DESCRIPTION_LENGTH = 500;

/**
 * Detect suspicious patterns that may indicate prompt injection attempts.
 *
 * @param text - Text to analyze for suspicious patterns
 * @returns True if suspicious patterns are detected
 */
export function detectSuspiciousPatterns(text: string): boolean {
  if (!text) return false;

  const suspiciousPatterns = [
    /\bignore\s+(all\s+)?(previous|prior|above|below)\s+instructions?\b/i,
    /\boverride\s+(all\s+)?(previous|prior|above|below)\s+instructions?\b/i,
    /\bsystem\s*:\s*/i,
    /\bSYSTEM\s*:\s*/i,
    /\bassistant\s*:\s*/i,
    /\bASSISTANT\s*:\s*/i,
    /\buser\s*:\s*/i,
    /\bUSER\s*:\s*/i,
    /\bforget\s+(all\s+)?(previous|prior|above|below)\s+instructions?\b/i,
    /\bdisregard\s+(all\s+)?(previous|prior|above|below)\s+instructions?\b/i,
    /\bnew\s+instructions?\s*:\s*/i,
    /\bNEW\s+INSTRUCTIONS?\s*:\s*/i,
    /\bexecute\s+(the\s+)?following\s+commands?\b/i,
    /\bdo\s+not\s+follow\s+(the\s+)?(previous|prior|above|below)\s+instructions?\b/i,
  ];

  for (const pattern of suspiciousPatterns) {
    if (pattern.test(text)) {
      return true;
    }
  }

  return false;
}

/**
 * Sanitize PR title or description input to prevent prompt injection attacks.
 *
 * This function implements multi-layer sanitization:
 * - Escapes curly braces to prevent template injection
 * - Escapes newlines to prevent prompt breakouts
 * - Escapes backticks to prevent code block injection
 * - Escapes delimiter markers to prevent delimiter confusion
 * - Normalizes whitespace
 * - Truncates to safe length limits
 * - Removes control characters
 *
 * Security considerations:
 * - All user input from PR metadata should be sanitized before use in prompts
 * - This function does not guarantee complete protection but significantly reduces risk
 * - Suspicious patterns are detected and logged but input is still sanitized
 *
 * @param text - Text to sanitize
 * @param maxLength - Maximum allowed length (defaults to MAX_DESCRIPTION_LENGTH)
 * @returns Sanitized text safe for use in prompts
 */
export function sanitizePrInput(
  text: string,
  maxLength: number = MAX_DESCRIPTION_LENGTH
): string {
  if (!text) {
    return "";
  }

  // Detect and log suspicious patterns
  if (detectSuspiciousPatterns(text)) {
    console.warn(
      "Suspicious pattern detected in PR input. Sanitizing and proceeding."
    );
  }

  let sanitized = text;

  // Remove control characters (except newlines which we'll handle separately)
  sanitized = sanitized.replace(/[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]/g, "");

  // Escape newlines to prevent prompt breakouts
  sanitized = sanitized
    .replace(/\r\n/g, " ")
    .replace(/\n/g, " ")
    .replace(/\r/g, " ");

  // Escape backticks to prevent code block injection
  sanitized = sanitized.replace(/`/g, "\\`");

  // Escape curly braces to prevent template injection
  sanitized = sanitized.replace(/{/g, "{{").replace(/}/g, "}}");

  // Escape delimiter markers to prevent delimiter confusion
  // Escape old delimiter pattern
  sanitized = sanitized.replace(/!!!/g, "\\!\\!\\!");
  // Escape new bracket-based delimiter patterns
  sanitized = sanitized.replace(/\[PR_TITLE_START\]/g, "\\[PR_TITLE_START\\]");
  sanitized = sanitized.replace(/\[PR_TITLE_END\]/g, "\\[PR_TITLE_END\\]");
  sanitized = sanitized.replace(/\[PR_DESC_START\]/g, "\\[PR_DESC_START\\]");
  sanitized = sanitized.replace(/\[PR_DESC_END\]/g, "\\[PR_DESC_END\\]");

  // Normalize whitespace: collapse multiple spaces/tabs into single space
  sanitized = sanitized.replace(/[ \t]+/g, " ");

  // Trim leading and trailing whitespace
  sanitized = sanitized.trim();

  // Truncate to max length
  if (sanitized.length > maxLength) {
    sanitized = sanitized.slice(0, maxLength - 3) + "...";
  }

  return sanitized;
}

/**
 * Validate and fix enum values in the analysis result.
 */
export function validateAndFixEnums(
  data: Partial<VisualAnalysisResult>
): VisualAnalysisResult {
  const validStatusEnum = ["pass", "fail", "warning", "none"] as const;
  const validCriticalIssuesEnum = [
    "none",
    "missing_sections",
    "other_issues",
  ] as const;
  const validVisualChangesEnum = ["none", "minor", "significant"] as const;
  const validRecommendationEnum = [
    "pass",
    "review_required",
    "reject",
  ] as const;
  const validSectionStatus = ["Present", "Missing"] as const;

  // Validate and fix status_enum
  if (!data.status_enum || !validStatusEnum.includes(data.status_enum as any)) {
    console.warn(
      `Invalid status_enum: ${data.status_enum}, defaulting to 'warning'`
    );
    data.status_enum = "warning";
    data.status = "warning";
  } else {
    // Ensure status matches status_enum
    data.status = data.status_enum;
  }

  // Validate and fix critical_issues_enum
  if (
    !data.critical_issues_enum ||
    !validCriticalIssuesEnum.includes(data.critical_issues_enum as any)
  ) {
    console.warn(
      `Invalid critical_issues_enum: ${data.critical_issues_enum}, defaulting to 'other_issues'`
    );
    data.critical_issues_enum = "other_issues";
  }

  // Validate and fix visual_changes_enum
  if (
    !data.visual_changes_enum ||
    !validVisualChangesEnum.includes(data.visual_changes_enum as any)
  ) {
    console.warn(
      `Invalid visual_changes_enum: ${data.visual_changes_enum}, defaulting to 'minor'`
    );
    data.visual_changes_enum = "minor";
  }

  // Validate and fix recommendation_enum
  if (
    !data.recommendation_enum ||
    !validRecommendationEnum.includes(data.recommendation_enum as any)
  ) {
    console.warn(
      `Invalid recommendation_enum: ${data.recommendation_enum}, defaulting to 'review_required'`
    );
    data.recommendation_enum = "review_required";
  }

  // Validate section status values
  if (data.critical_issues?.sections) {
    for (const section of data.critical_issues.sections) {
      if (
        !section.status ||
        !validSectionStatus.includes(section.status as any)
      ) {
        console.warn(
          `Invalid section status: ${section.status}, defaulting to 'Present'`
        );
        section.status = "Present";
      }
    }
  }

  return data as VisualAnalysisResult;
}

/**
 * Generate metadata (UUID, timestamps).
 */
export function generateMetadata(): {
  id: string;
  timestamp: string;
  created_at: string;
} {
  const now = new Date().toISOString();
  return {
    id: uuidv4(),
    timestamp: now,
    created_at: now,
  };
}
