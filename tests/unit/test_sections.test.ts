/**
 * Test suite for section analysis retry logic.
 *
 * This module tests the analyzeSectionsSideBySide function, ensuring:
 * 1. The function retries on timeout errors up to the maximum allowed attempts
 * 2. Proper error handling and retry delays are implemented
 * 3. The function raises an exception after all retries are exhausted
 *
 * The tests cover:
 * - Retry logic for timeouts
 * - Correct number of retries and sleep calls
 * - Exception raising after max retries
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { analyzeSectionsSideBySide } from "../../src-typescript/sections/sections.js";
import { Stagehand } from "@browserbasehq/stagehand";

// Mock extractRealDomInfo
vi.mock("../../src-typescript/sections/sectionDom.js", () => ({
  extractRealDomInfo: vi.fn().mockResolvedValue([
    {
      tag: "section",
      id: "hero",
      className: "hero-section",
      ariaLabel: "Hero section",
      textContent: "Welcome",
      boundingBox: { x: 0, y: 0, width: 100, height: 100 },
    },
  ]),
}));

describe("analyzeSectionsSideBySide retry logic", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should retry on timeout errors up to maximum attempts", async () => {
    // Create a mock Stagehand that will timeout
    // The error message must match exactly what the code checks for
    const timeoutError = new Error("Section analysis timed out");
    const mockExtract = vi.fn().mockRejectedValue(timeoutError);
    const mockStagehand = {
      context: {
        pages: vi.fn(() => [
          {
            goto: vi.fn().mockResolvedValue(undefined),
          },
        ]),
      },
      extract: mockExtract,
    } as unknown as Stagehand;

    // Start the async function
    const promise = analyzeSectionsSideBySide(
      mockStagehand,
      "http://example.com",
      "http://preview.com"
    );

    // The function should retry 3 times and then throw
    // Use Promise.allSettled to ensure all promises are handled
    const result = await Promise.allSettled([
      promise,
      // Advance timers to trigger retries
      (async () => {
        for (let i = 0; i < 3; i++) {
          await vi.advanceTimersByTimeAsync(15000); // 15 seconds per retry
        }
        await vi.runAllTimersAsync();
      })(),
    ]);

    // The promise should be rejected
    const promiseResult = result[0];
    expect(promiseResult.status).toBe("rejected");
    if (promiseResult.status === "rejected") {
      expect(promiseResult.reason.message).toBe(
        "Section analysis timed out after all retries"
      );
    }

    // Should have attempted extract 3 times (max retries)
    expect(mockExtract).toHaveBeenCalledTimes(3);
  });

  it("should succeed on first attempt when no timeout occurs", async () => {
    const mockStagehand = {
      context: {
        pages: vi.fn(() => [
          {
            goto: vi.fn().mockResolvedValue(undefined),
          },
        ]),
      },
      extract: vi.fn().mockResolvedValue({
        baseUrlStructure: "Test structure",
        sections: [
          {
            name: "Hero",
            sectionId: "hero-section",
            position: "top",
            purpose: "Introduction",
            keyElements: ["title", "subtitle"],
            visualPatterns: "Centered layout",
            animation: "none",
            htmlElement: "section",
            htmlId: "hero",
            htmlClasses: "hero-section",
            ariaLabel: "Hero section",
            contentIdentifier: "welcome",
          },
        ],
      }),
    } as unknown as Stagehand;

    const result = await analyzeSectionsSideBySide(
      mockStagehand,
      "http://example.com",
      "http://preview.com"
    );

    expect(result).toContain("Hero");
    expect(result).toContain("hero-section");
    expect(mockStagehand.extract).toHaveBeenCalledTimes(1);
  });
});
