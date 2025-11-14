import type { VisualAnalysisResult } from "../../../dist/vision/types.js";

/**
 * Input parameters for compare_urls tool.
 */
export interface CompareUrlsInput {
  baseUrl: string;
  previewUrl: string;
  page?: string;
}

/**
 * Image paths returned from comparison.
 */
export interface ComparisonImages {
  base_screenshot: string;
  preview_screenshot: string;
  diff_image: string;
  section_screenshots?: Record<string, { base: string; preview: string }>;
}

/**
 * Output structure for compare_urls tool.
 */
export interface CompareUrlsOutput {
  status: "pass" | "fail" | "warning" | "none";
  visual_analysis: VisualAnalysisResult;
  sections_analysis: string;
  images: ComparisonImages;
}
