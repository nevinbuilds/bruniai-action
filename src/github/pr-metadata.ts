/**
 * GitHub PR metadata utilities.
 * Functions for fetching PR title and description from GitHub API.
 */

import { getGithubAppToken } from "./auth.js";
import { getPrNumberFromEvent } from "./pr-comments.js";

/**
 * PR metadata response from GitHub API.
 */
interface PrMetadata {
  title: string | null;
  description: string | null;
}

/**
 * GitHub PR API response structure.
 */
interface GitHubPrResponse {
  title?: string;
  body?: string;
}

/**
 * Fetch PR metadata (title and description) from GitHub API.
 * Equivalent to Python's fetch_pr_metadata().
 *
 * @returns Object with title and description, or null values if fetch fails
 */
export async function fetchPrMetadata(): Promise<PrMetadata> {
  // Get GitHub App token
  const githubToken = getGithubAppToken();
  if (!githubToken) {
    console.error("Failed to get GitHub App token");
    return { title: null, description: null };
  }

  const repo = process.env.GITHUB_REPOSITORY;
  const prNumberEnv = process.env.PR_NUMBER;
  let prNumber: number | null = null;

  if (prNumberEnv) {
    const parsed = parseInt(prNumberEnv, 10);
    prNumber = isNaN(parsed) ? null : parsed;
  } else {
    prNumber = await getPrNumberFromEvent();
  }

  if (!githubToken || !repo || !prNumber) {
    console.warn(
      "Cannot fetch PR metadata: missing token, repo, or PR number"
    );
    return { title: null, description: null };
  }

  const headers = {
    Authorization: `token ${githubToken}`,
    Accept: "application/vnd.github.v3+json",
  };

  const url = `https://api.github.com/repos/${repo}/pulls/${prNumber}`;

  try {
    const response = await fetch(url, { headers });

    if (response.status === 200) {
      const data = (await response.json()) as GitHubPrResponse;
      return {
        title: data.title || null,
        description: data.body || null,
      };
    } else {
      const errorText = await response.text();
      console.error(
        `Failed to fetch PR metadata: ${response.status} ${errorText}`
      );
      return { title: null, description: null };
    }
  } catch (error) {
    console.error("Error fetching PR metadata:", error);
    return { title: null, description: null };
  }
}

