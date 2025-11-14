import { Stagehand } from "@browserbasehq/stagehand";
import { performComparison } from "../comparison/core.js";
import type { CompareUrlsInput, CompareUrlsOutput } from "./types.js";
import { join } from "path";
import { mkdirSync, existsSync } from "fs";
import { tmpdir } from "os";

/**
 * Compare two URLs visually and return analysis results.
 *
 * This function wraps the core comparison logic with MCP-specific setup:
 * - Creates a temporary directory for images
 * - Manages Stagehand lifecycle
 * - Formats output for MCP tool response
 *
 * @param input - Comparison input parameters
 * @returns Complete analysis results with image paths
 */
export async function compareUrls(
  input: CompareUrlsInput
): Promise<CompareUrlsOutput> {
  const { baseUrl, previewUrl, page = "/" } = input;

  // Create temporary directory for images.
  const imagesDir = join(tmpdir(), `bruniai-${Date.now()}`);
  if (!existsSync(imagesDir)) {
    mkdirSync(imagesDir, { recursive: true });
  }

  // Initialize Stagehand.
  const stagehand = new Stagehand({
    env: "LOCAL",
    localBrowserLaunchOptions: {
      headless: true,
    },
  });

  try {
    await stagehand.init();

    // Perform the core comparison.
    const result = await performComparison({
      stagehand,
      baseUrl,
      previewUrl,
      page,
      imagesDir,
      // MCP doesn't need PR metadata.
    });

    // Build output structure matching MCP tool format.
    const output: CompareUrlsOutput = {
      status: result.visual_analysis.status,
      visual_analysis: result.visual_analysis,
      sections_analysis: result.sections_analysis,
      images: {
        base_screenshot: result.base_screenshot,
        preview_screenshot: result.preview_screenshot,
        diff_image: result.diff_image,
        section_screenshots:
          Object.keys(result.section_screenshots).length > 0
            ? Object.fromEntries(
                Object.entries(result.section_screenshots).map(
                  ([key, value]) => [
                    key,
                    { base: value.base, preview: value.preview },
                  ]
                )
              )
            : undefined,
      },
    };

    return output;
  } finally {
    await stagehand.close();
  }
}
