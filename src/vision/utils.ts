import { v4 as uuidv4 } from "uuid";
import type { VisualAnalysisResult } from "./types.js";

/**
 * Escape curly braces in a string to prevent template injection.
 */
export function escapeCurlyBraces(text: string): string {
  return text.replace(/{/g, "{{").replace(/}/g, "}}");
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
  if (
    !data.status_enum ||
    !validStatusEnum.includes(data.status_enum as any)
  ) {
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
      if (!section.status || !validSectionStatus.includes(section.status as any)) {
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

