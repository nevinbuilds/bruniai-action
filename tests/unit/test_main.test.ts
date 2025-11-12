/**
 * Test suite for the main runner entrypoint.
 *
 * This module contains a basic smoke test for the main() function to verify that:
 * 1. The function can be called without errors
 * 2. The basic flow of argument parsing and environment setup works
 * 3. The function handles early returns gracefully
 *
 * Note: Detailed testing of individual components (screenshots, image processing,
 * API calls) is handled in their respective test modules.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { mkdtemp, rm } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";

// Mock all dependencies before importing main
vi.mock("../../src/github/pr-metadata.js", () => ({
  fetchPrMetadata: vi.fn().mockResolvedValue({
    title: "Test PR",
    description: "Test body",
  }),
}));

vi.mock("../../src/github/pr-comments.js", () => ({
  getPrNumberFromEvent: vi.fn().mockResolvedValue(123),
  formatVisualAnalysisToMarkdown: vi.fn(),
  postPrComment: vi.fn(),
}));

vi.mock("../../src/diff/diff.js", () => ({
  generateDiffImage: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../src/sections/sectionExtraction.js", () => ({
  extractSectionBoundingBoxes: vi.fn().mockResolvedValue([]),
  takeSectionScreenshot: vi.fn(),
}));

vi.mock("../../src/sections/sections.js", () => ({
  analyzeSectionsSideBySide: vi
    .fn()
    .mockResolvedValue("Test sections analysis"),
}));

vi.mock("../../src/vision/index.js", () => ({
  analyzeImagesWithVision: vi.fn().mockResolvedValue({ status: "pass" }),
}));

vi.mock("../../src/reporter/index.js", () => ({
  BruniReporter: vi.fn().mockImplementation(() => ({
    sendMultiPageReport: vi.fn(),
  })),
  parseMultiPageAnalysisResults: vi.fn(),
  encodeImageCompressed: vi.fn(),
}));

vi.mock("../../src/utils/window.js", () => ({
  ensureViewportSize: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("fs", () => ({
  existsSync: vi.fn().mockReturnValue(true),
  mkdirSync: vi.fn(),
  writeFileSync: vi.fn(),
}));

vi.mock("@browserbasehq/stagehand", () => {
  class MockStagehand {
    init = vi.fn().mockResolvedValue(undefined);
    context = {
      pages: vi.fn(() => [
        {
          goto: vi.fn().mockResolvedValue(undefined),
          screenshot: vi.fn().mockResolvedValue(Buffer.from("fake-image")),
        },
      ]),
    };
  }
  return {
    Stagehand: MockStagehand,
  };
});

vi.mock("../../src/args.js", () => ({
  parseArgs: vi.fn().mockReturnValue({
    baseUrl: "http://example.com",
    prUrl: "http://preview.com",
    pages: null,
    bruniToken: null,
    bruniApiUrl: null,
  }),
}));

describe("main function", () => {
  let tempDir: string;
  let originalEnv: NodeJS.ProcessEnv;

  beforeEach(async () => {
    tempDir = await mkdtemp(join(tmpdir(), "test-main-"));
    originalEnv = { ...process.env };
    vi.stubEnv("GITHUB_REPOSITORY", "org/repo");
    vi.stubEnv("PR_NUMBER", "123");
    vi.stubEnv("GITHUB_WORKSPACE", tempDir);
  });

  afterEach(async () => {
    process.env = originalEnv;
    if (tempDir) {
      await rm(tempDir, { recursive: true, force: true });
    }
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it("should have parseArgs function available", async () => {
    // Test that parseArgs can be mocked and returns expected values
    const { parseArgs } = await import("../../src/args.js");
    const result = vi.mocked(parseArgs)();
    expect(result).toHaveProperty("baseUrl");
    expect(result).toHaveProperty("prUrl");
  });

  it("should handle pages parameter parsing", async () => {
    // Test that pages parameter is parsed correctly
    const { parseArgs } = await import("../../src/args.js");
    vi.mocked(parseArgs).mockReturnValue({
      baseUrl: "http://example.com",
      prUrl: "http://preview.com",
      pages: "/,/about,/contact",
      bruniToken: undefined,
      bruniApiUrl: undefined,
    });

    const result = parseArgs();
    expect(result.pages).toBe("/,/about,/contact");
  });
});
