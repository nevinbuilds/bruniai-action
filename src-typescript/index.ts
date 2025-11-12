import "dotenv/config";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod/v3";
import { fetchPrMetadata } from "./github/pr-metadata.js";
import { getPrNumberFromEvent } from "./github/pr-comments.js";
import { parseArgs } from "./args.js";
import { generateDiffImage } from "./diff/diff.js";

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

  pages.forEach(async (page) => {
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

    await stagehand.init();
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

    // Act on the page
    // await stagehand.act("Click the learn more button");

    // Extract structured data
    const extractedDescription = await stagehand.extract(
      "Extract the main heading or title text visible on this page",
      z.string()
    );

    console.log(extractedDescription);
    await stagehand.close();

    // Signal to exit the action successfully.
    process.exit(0);
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
