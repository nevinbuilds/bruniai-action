import "dotenv/config";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod/v3";
import { fetchPrMetadata } from "./github/pr-metadata.js";
import { getPrNumberFromEvent } from "./github/pr-comments.js";

async function main() {
  // Example: Collect PR metadata similar to Python implementation
  const { title, description } = await fetchPrMetadata();
  const repo = process.env.GITHUB_REPOSITORY;
  const prNumberEnv = process.env.PR_NUMBER;
  let prNumber: number | null = null;

  if (prNumberEnv) {
    const parsed = parseInt(prNumberEnv, 10);
    prNumber = isNaN(parsed) ? null : parsed;
  } else {
    prNumber = await getPrNumberFromEvent();
  }

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
