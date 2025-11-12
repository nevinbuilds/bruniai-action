import "dotenv/config";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod/v3";
import { fetchPrMetadata } from "./github/pr-metadata.js";
import { getPrNumberFromEvent } from "./github/pr-comments.js";
import { parseArgs } from "./args";

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

  await stagehand.init();
  const page = stagehand.context.pages()[0];

  await page.goto("https://example.com");

  // Act on the page
  await stagehand.act("Click the learn more button");

  // Extract structured data
  const extractedDescription = await stagehand.extract(
    "extract the description",
    z.string()
  );

  console.log(extractedDescription);
  await stagehand.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
