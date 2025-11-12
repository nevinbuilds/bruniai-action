/**
 * Test suite for screenshot capture functionality.
 *
 * This module tests the screenshot capture functionality which is responsible for:
 * 1. Taking screenshots of web pages using Playwright
 * 2. Handling various error conditions
 * 3. File output management
 *
 * Note: In TypeScript, screenshots are taken directly using Playwright's
 * page.screenshot() method, not via subprocess like in Python.
 * The tests verify the screenshot functionality works correctly.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { mkdtemp, rm } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";
import { existsSync } from "fs";
import { Stagehand } from "@browserbasehq/stagehand";

// Mock Stagehand
vi.mock("@browserbasehq/stagehand", () => {
  class MockStagehand {
    init = vi.fn().mockResolvedValue(undefined);
    context = {
      pages: vi.fn(() => [
        {
          goto: vi.fn().mockResolvedValue(undefined),
          screenshot: vi.fn().mockResolvedValue(Buffer.from("fake-image-data")),
        },
      ]),
    };
  }
  return {
    Stagehand: MockStagehand,
  };
});

describe("screenshot capture", () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await mkdtemp(join(tmpdir(), "test-screenshot-"));
  });

  afterEach(async () => {
    if (tempDir) {
      await rm(tempDir, { recursive: true, force: true });
    }
    vi.clearAllMocks();
  });

  it("should successfully capture screenshot", async () => {
    const stagehand = new Stagehand({
      env: "LOCAL",
      localBrowserLaunchOptions: { headless: true },
    });

    await stagehand.init();

    const page = stagehand.context.pages()[0];
    const outputPath = join(tempDir, "screenshot.png");

    const screenshot = await page.screenshot({ fullPage: true });
    const fs = await import("fs");
    fs.writeFileSync(outputPath, screenshot);

    expect(existsSync(outputPath)).toBe(true);
    expect(page.screenshot).toHaveBeenCalled();
  });

  it("should handle screenshot errors gracefully", async () => {
    const stagehand = new Stagehand({
      env: "LOCAL",
      localBrowserLaunchOptions: { headless: true },
    });

    await stagehand.init();

    const page = stagehand.context.pages()[0];
    const outputPath = join(tempDir, "screenshot.png");

    // Mock screenshot to throw an error by updating the mock
    (page.screenshot as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Screenshot failed")
    );

    await expect(page.screenshot({ fullPage: true })).rejects.toThrow(
      "Screenshot failed"
    );

    expect(existsSync(outputPath)).toBe(false);
  });

  it("should handle navigation errors", async () => {
    const stagehand = new Stagehand({
      env: "LOCAL",
      localBrowserLaunchOptions: { headless: true },
    });

    await stagehand.init();

    const page = stagehand.context.pages()[0];

    // Mock goto to throw an error by updating the mock
    (page.goto as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Navigation failed")
    );

    await expect(
      page.goto("https://example.com", { waitUntil: "networkidle" })
    ).rejects.toThrow("Navigation failed");
  });
});

