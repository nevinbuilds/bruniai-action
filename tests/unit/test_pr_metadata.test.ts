/**
 * Test suite for GitHub PR metadata functionality.
 *
 * This module tests the PR metadata fetching function which is responsible for:
 * 1. Retrieving PR title and description from GitHub
 * 2. Managing GitHub API interactions
 * 3. Handling authentication and environment variables
 * 4. Processing API responses
 *
 * The tests cover:
 * - Successful metadata retrieval
 * - API response handling
 * - Environment variable management
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchPrMetadata } from "../../src-typescript/github/pr-metadata.js";

// Mock fetch globally
global.fetch = vi.fn();

// Mock auth module
vi.mock("../../src-typescript/github/auth.js", () => ({
  getGithubAppToken: vi.fn().mockReturnValue("fake_token"),
}));

// Mock pr-comments module
vi.mock("../../src-typescript/github/pr-comments.js", () => ({
  getPrNumberFromEvent: vi.fn().mockResolvedValue(123),
}));

describe("fetchPrMetadata", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("GITHUB_REPOSITORY", "org/repo");
    vi.stubEnv("PR_NUMBER", "123");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("should successfully retrieve PR metadata", async () => {
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>;
    mockFetch.mockResolvedValue({
      status: 200,
      json: async () => ({ title: "Test PR", body: "Test body" }),
    });

    const { title, description } = await fetchPrMetadata();

    expect(title).toBe("Test PR");
    expect(description).toBe("Test body");
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.github.com/repos/org/repo/pulls/123",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "token fake_token",
        }),
      })
    );
  });
});

