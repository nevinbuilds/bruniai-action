import "dotenv/config";
import { Stagehand } from "@browserbasehq/stagehand";
import { fetchPrMetadata } from "./github/pr-metadata.js";
import {
  getPrNumberFromEvent,
  formatVisualAnalysisToMarkdown,
  postPrComment,
} from "./github/pr-comments.js";
import { parseArgs } from "./args.js";
import { generateDiffImage } from "./diff/diff.js";
import { analyzeSectionsSideBySide } from "./sections/sections.js";
import {
  extractSectionBoundingBoxes,
  takeSectionScreenshot,
} from "./sections/sectionExtraction.js";
import { analyzeImagesWithVision } from "./vision/index.js";

async function main() {
  // Parse command-line arguments
  const args = parseArgs();

  if (!args.baseUrl || !args.prUrl) {
    console.error("Error: --base-url and --pr-url are required");
    process.exit(1);
  }

  // Example: Collect PR metadata similar to Python implementation
  const { title, description } = await fetchPrMetadata();
  const repo = process.env.GITHUB_REPOSITORY;
  const prNumberEnv = process.env.PR_NUMBER;
  let prNumber: number | null = null;

  // Parse pages argument (comma-separated format: "/,/contact")
  let pages: string[] = ["/"]; // Default to homepage
  if (args.pages) {
    pages = args.pages
      .split(",")
      .map((p) => p.trim())
      .filter((p) => p);
  }
  console.log("Pages:", pages);

  if (prNumberEnv) {
    const parsed = parseInt(prNumberEnv, 10);
    prNumber = isNaN(parsed) ? null : parsed;
  } else {
    prNumber = await getPrNumberFromEvent();
  }

  console.log("Base URL:", args.baseUrl);
  console.log("PR URL:", args.prUrl);
  console.log("PR Title:", title);
  console.log("PR Description:", description);
  console.log("Repository:", repo);
  console.log("PR Number:", prNumber);

  const stagehand = new Stagehand({
    env: "LOCAL",
    localBrowserLaunchOptions: {
      headless: true,
    },
  });

  const GITHUB_WORKSPACE = process.env.GITHUB_WORKSPACE || process.cwd();
  const path = await import("path");
  const fs = await import("fs");
  const imagesDir = path.join(GITHUB_WORKSPACE, "images");
  if (!fs.existsSync(imagesDir)) {
    fs.mkdirSync(imagesDir, { recursive: true });
  }

  // Initialize stagehand once before processing pages.
  await stagehand.init();

  // Store all analyses for final summary
  const allAnalyses: Array<{
    page_path: string;
    visual_analysis: Awaited<ReturnType<typeof analyzeImagesWithVision>>;
    sections_analysis: string;
  }> = [];

  // Process each page sequentially to avoid race conditions.
  for (const page of pages) {
    console.log("Processing page ------ ", page);

    // Construct full URLs for this page
    const baseUrl = args.baseUrl!.replace(/\/$/, "") + page;
    const prUrl = args.prUrl!.replace(/\/$/, "") + page;

    console.log(`Base URL: ${baseUrl}`);
    console.log(`PR URL: ${prUrl}`);

    // Define screenshot paths with page-specific names
    // Remove all slashes for file suffix, or use 'home' for root
    let pageSuffix = page.replace(/\//g, "_");
    pageSuffix = pageSuffix === "_" ? "home" : pageSuffix;

    const stagehandPage = stagehand.context.pages()[0];

    await stagehandPage.goto(`${baseUrl}`);

    const baseScreenshot = await stagehandPage.screenshot({
      fullPage: true,
    });

    fs.writeFileSync(
      path.join(imagesDir, `base_screenshot_${pageSuffix}.png`),
      baseScreenshot
    );

    await stagehandPage.goto(`${prUrl}`);
    const prScreenshot = await stagehandPage.screenshot({
      fullPage: true,
    });

    fs.writeFileSync(
      path.join(imagesDir, `pr_screenshot_${pageSuffix}.png`),
      prScreenshot
    );

    await generateDiffImage(
      path.join(imagesDir, `base_screenshot_${pageSuffix}.png`),
      path.join(imagesDir, `pr_screenshot_${pageSuffix}.png`),
      path.join(imagesDir, `diff_${pageSuffix}.png`)
    );

    // Analyze sections and get formatted analysis output.
    const sectionsAnalysis = await analyzeSectionsSideBySide(
      stagehand,
      baseUrl,
      prUrl
    );

    // Extract section bounding boxes with IDs from analysis.
    const sectionsWithIds = await extractSectionBoundingBoxes(
      stagehand,
      baseUrl,
      sectionsAnalysis
    );
    console.log(
      `Extracted ${sectionsWithIds.length} sections with IDs from ${baseUrl}`
    );

    // Capture section screenshots for both base and PR URLs.
    const sectionScreenshots: Record<string, { base: string; pr: string }> = {};
    for (const section of sectionsWithIds) {
      const sectionId = section.sectionId;

      // Define section screenshot paths.
      const baseSectionScreenshot = path.join(
        imagesDir,
        `base_screenshot_${pageSuffix}_section_${sectionId}.png`
      );
      const prSectionScreenshot = path.join(
        imagesDir,
        `pr_screenshot_${pageSuffix}_section_${sectionId}.png`
      );

      // Take section screenshots using section IDs and analysis data.
      const baseSectionSuccess = await takeSectionScreenshot(
        stagehand,
        baseUrl,
        baseSectionScreenshot,
        sectionId,
        sectionsAnalysis
      );
      const prSectionSuccess = await takeSectionScreenshot(
        stagehand,
        prUrl,
        prSectionScreenshot,
        sectionId,
        sectionsAnalysis
      );

      if (baseSectionSuccess && prSectionSuccess) {
        sectionScreenshots[sectionId] = {
          base: baseSectionScreenshot,
          pr: prSectionScreenshot,
        };
        console.log(`Captured section screenshots for ${sectionId}`);
      } else {
        console.warn(`Failed to capture section screenshots for ${sectionId}`);
      }
    }

    // Perform visual analysis with the sections information
    const visualAnalysis = await analyzeImagesWithVision(
      path.join(imagesDir, `base_screenshot_${pageSuffix}.png`),
      path.join(imagesDir, `pr_screenshot_${pageSuffix}.png`),
      path.join(imagesDir, `diff_${pageSuffix}.png`),
      baseUrl,
      prUrl,
      prNumber?.toString() || "",
      repo || "",
      sectionsAnalysis,
      title || undefined,
      description || undefined
    );

    console.log("Visual analysis completed:", visualAnalysis.status);

    // Store the analysis results
    allAnalyses.push({
      page_path: page,
      visual_analysis: visualAnalysis,
      sections_analysis: sectionsAnalysis,
    });
  }

  // Close stagehand after all pages are processed.
  await stagehand.close();

  // Combine all analyses into a comprehensive report
  let finalSummary =
    "Information about visual testing analysis provided by [bruniai](https://www.brunivisual.com/)\n\n" +
    `**Testing Summary**: ${allAnalyses.length} page${
      allAnalyses.length !== 1 ? "s" : ""
    } analyzed\n\n`;

  for (let i = 0; i < allAnalyses.length; i++) {
    const pageAnalysis = allAnalyses[i];
    const pagePath = pageAnalysis.page_path;
    const visualAnalysis = pageAnalysis.visual_analysis;
    const sectionsAnalysis = pageAnalysis.sections_analysis;

    // Format the visual analysis for this page
    const formattedVisualAnalysis =
      formatVisualAnalysisToMarkdown(visualAnalysis);

    // Add page-specific section
    const pageSummary =
      `<details>\n` +
      `<summary>Page ${i + 1}: ${pagePath}</summary>\n\n` +
      `<details>\n` +
      `<summary>Structural Analysis</summary>\n\n` +
      `${sectionsAnalysis}\n` +
      `</details>\n\n` +
      `${formattedVisualAnalysis}\n` +
      `</details>\n\n`;

    finalSummary += pageSummary;
  }

  // Post to GitHub
  await postPrComment(finalSummary);
  console.log("Complete analysis has been logged above.");
}

main()
  .then(() => {
    console.log("Done");
    process.exit(0);
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
