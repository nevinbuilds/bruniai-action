/**
 * GitHub PR comment utilities.
 * Functions for extracting PR numbers from GitHub event files.
 */

import { readFile } from "fs/promises";

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
    console.warn(
      "GITHUB_EVENT_PATH not found or GITHUB_REPOSITORY not set."
    );
    return null;
  }

  try {
    const eventContent = await readFile(eventPath, "utf-8");
    const event: GitHubEvent = JSON.parse(eventContent);

    const prNumber =
      event.pull_request?.number || event.issue?.number || null;

    if (!prNumber) {
      console.warn("PR number not found in event payload.");
    }
    return prNumber;
  } catch (error) {
    console.error("Error reading PR number from event:", error);
    return null;
  }
}

