/**
 * Test suite for section bounding box extraction error handling.
 *
 * This module tests the error handling behavior of extractSectionBoundingBoxes
 * when network errors occur.
 *
 * This test verifies that the function gracefully handles network errors during
 * browser launch by returning an empty list instead of propagating the exception.
 * This is important for:
 * 1. Ensuring the visual testing pipeline continues even when network issues occur
 * 2. Preventing cascading failures in the testing system
 * 3. Maintaining a consistent return type (list) even in error cases
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { extractSectionBoundingBoxes } from "../../src-typescript/sections/sectionExtraction.js";
import { Stagehand } from "@browserbasehq/stagehand";

describe("extractSectionBoundingBoxes error handling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return empty array when network errors occur", async () => {
    // Create a mock Stagehand instance that will simulate a network error.
    // This simulates what would happen if the browser couldn't be launched due
    // to network issues.
    const mockStagehand = {
      context: {
        pages: vi.fn(() => [
          {
            goto: vi.fn().mockRejectedValue(new Error("Network error")),
          },
        ]),
      },
    } as unknown as Stagehand;

    // Call the function with a test URL.
    // Even though we're using a real URL, the mock will prevent actual network
    // calls.
    const result = await extractSectionBoundingBoxes(
      mockStagehand,
      "https://example.com"
    );

    // Verify that the function returns an empty list when network errors occur.
    // This is the expected behavior for graceful error handling.
    expect(result).toEqual([]);
  });
});
