/**
 * GitHub authentication utilities.
 * Retrieves GitHub token from environment variables.
 */

/**
 * Get the GitHub Actions token from the environment.
 * Equivalent to Python's get_github_app_token().
 *
 * @returns GitHub token string, or null if not found
 */
export function getGithubAppToken(): string | null {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error("Missing GITHUB_TOKEN environment variable");
    return null;
  }
  return token;
}
