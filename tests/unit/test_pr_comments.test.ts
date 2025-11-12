/**
 * Test suite for GitHub PR comment functionality.
 *
 * This module tests the PR comment management functions which are responsible for:
 * 1. Posting and updating comments on GitHub Pull Requests
 * 2. Extracting PR numbers from GitHub event data
 * 3. Managing GitHub API interactions
 * 4. Handling authentication and environment variables
 *
 * The tests cover various scenarios:
 * - Updating existing comments
 * - Creating new comments
 * - Extracting PR information from GitHub events
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { readFile } from "fs/promises";
import {
  postPrComment,
  getPrNumberFromEvent,
  formatVisualAnalysisToMarkdown,
} from "../../src/github/pr-comments.js";

// Mock fetch globally
global.fetch = vi.fn();

// Mock fs/promises
vi.mock("fs/promises", () => ({
  readFile: vi.fn(),
}));

// Mock auth module
vi.mock("../../src/github/auth.js", () => ({
  getGithubAppToken: vi.fn().mockReturnValue("fake_token"),
}));

describe("PR comment functions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("GITHUB_REPOSITORY", "org/repo");
    vi.stubEnv("PR_NUMBER", "123");
    vi.stubEnv("GITHUB_RUN_ID", "456");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("should update existing PR comment", async () => {
    // Mock fetch to return existing comment
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>;
    mockFetch
      .mockResolvedValueOnce({
        status: 200,
        json: async () => [
          {
            id: 1,
            body: "Information about visual testing analysis provided by [bruniai]",
          },
        ],
      })
      .mockResolvedValueOnce({
        status: 200,
        text: async () => "Updated",
      });

    const testVisualAnalysis = {
      overall_recommendation_enum: "pass",
      pages: [
        {
          page_name: "/",
          critical_issues: { sections: [] },
          visual_changes: {},
          structural_analysis: {},
        },
      ],
    };

    await postPrComment(
      formatVisualAnalysisToMarkdown(testVisualAnalysis as any)
    );

    expect(mockFetch).toHaveBeenCalledTimes(2);
    // First call should be GET to fetch comments
    expect(mockFetch).toHaveBeenNthCalledWith(
      1,
      "https://api.github.com/repos/org/repo/issues/123/comments",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "token fake_token",
        }),
      })
    );
    // Second call should be PATCH to update comment
    expect(mockFetch).toHaveBeenNthCalledWith(
      2,
      "https://api.github.com/repos/org/repo/issues/comments/1",
      expect.objectContaining({
        method: "PATCH",
      })
    );
  });

  it("should extract PR number from GitHub event", async () => {
    vi.stubEnv("GITHUB_EVENT_PATH", "/fake/path");
    vi.stubEnv("GITHUB_REPOSITORY", "org/repo");

    const mockReadFile = readFile as ReturnType<typeof vi.fn>;
    mockReadFile.mockResolvedValue('{"pull_request": {"number": 123}}');

    const prNumber = await getPrNumberFromEvent();

    expect(prNumber).toBe(123);
    expect(mockReadFile).toHaveBeenCalledWith("/fake/path", "utf-8");
  });

  it("should format single-page visual analysis to markdown", () => {
    const visualAnalysis = {
      critical_issues_enum: "none",
      visual_changes_enum: "minor",
      recommendation_enum: "pass",
      critical_issues: {
        sections: [
          { name: "Hero", status: "Present" },
          { name: "Footer", status: "Missing" },
        ],
        summary: "Footer is missing.",
      },
      visual_changes: {
        diff_highlights: ["Button color changed"],
        animation_issues: "Carousel animates.",
        conclusion: "Minor visual adjustments.",
      },
      structural_analysis: {
        section_order: "remains the same.",
        layout: "No major layout changes.",
        broken_layouts: "",
      },
    };

    const md = formatVisualAnalysisToMarkdown(
      visualAnalysis as any,
      "https://example.com/artifacts"
    );

    // Header reflects warning due to minor visual changes.
    expect(md).toContain("## ⚠️ Visual Testing Report — Warning");
    // Branding line.
    expect(md).toContain(
      "*1 page analyzed by [bruniai](https://www.brunivisual.com/)*"
    );
    // Artifacts link.
    expect(md).toContain("[📦 View Artifacts](https://example.com/artifacts)");
    // Critical sections table and entries.
    expect(md).toContain("### 🚨 Critical Sections Check");
    expect(md).toContain("Hero");
    expect(md).toContain("Footer");
    expect(md).toContain("❌"); // Missing footer row uses cross icon.
    expect(md).toContain("✅"); // Present hero row uses check icon.
    // Visual changes section and items.
    expect(md).toContain("### 🎨 Visual Changes");
    expect(md).toContain("- Button color changed");
    expect(md).toContain("- Carousel animates.");
    expect(md).toContain("- Minor visual adjustments.");
    // Structure section and details.
    expect(md).toContain("### 🏗️ Structure");
    expect(md).toContain("- Section order remains the same.");
    expect(md).toContain("- Layout No major layout changes.");
    // Collapsible reference block.
    expect(md).toContain("<details>");
    expect(md).toContain("</details>");
    expect(md).toContain("Reference Structure (click to expand)");
  });
});
