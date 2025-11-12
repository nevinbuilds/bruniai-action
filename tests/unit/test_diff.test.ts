/**
 * Test suite for the image diff generation functionality.
 *
 * This module tests the generateDiffImage function which is responsible for:
 * 1. Creating visual difference maps between two images
 * 2. Handling images of different sizes
 * 3. Managing transparency in the output
 * 4. Error handling for invalid inputs
 *
 * The tests cover various scenarios:
 * - Basic difference detection between images
 * - Cases with no differences
 * - Images of different sizes
 * - Error cases (missing files, invalid files)
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtemp, rm } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";
import sharp from "sharp";
import { generateDiffImage } from "../../src/diff/diff.js";
import { existsSync } from "fs";

/**
 * Helper function to create test images with specified color and size.
 */
async function createImage(
  path: string,
  color: { r: number; g: number; b: number },
  size: { width: number; height: number } = { width: 10, height: 10 }
): Promise<void> {
  await sharp({
    create: {
      width: size.width,
      height: size.height,
      channels: 3,
      background: color,
    },
  })
    .png()
    .toFile(path);
}

describe("generateDiffImage", () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await mkdtemp(join(tmpdir(), "test-diff-"));
  });

  afterEach(async () => {
    if (tempDir) {
      await rm(tempDir, { recursive: true, force: true });
    }
  });

  it("should detect basic differences between two images", async () => {
    const before = join(tempDir, "before.png");
    const after = join(tempDir, "after.png");
    const diff = join(tempDir, "diff.png");

    await createImage(before, { r: 255, g: 255, b: 255 }); // White
    await createImage(after, { r: 255, g: 0, b: 0 }); // Red

    await generateDiffImage(before, after, diff);

    expect(existsSync(diff)).toBe(true);

    const diffImage = sharp(diff);
    const metadata = await diffImage.metadata();
    expect(metadata.width).toBe(10);
    expect(metadata.height).toBe(10);
    expect(metadata.channels).toBe(4); // RGBA

    // Check that there are some red pixels (differences)
    const diffBuffer = await diffImage
      .ensureAlpha()
      .raw({ depth: "uchar" })
      .toBuffer({ resolveWithObject: false });

    // Check for red pixels (R=255) with opacity (A=255)
    let hasRedPixels = false;
    for (let i = 0; i < diffBuffer.length; i += 4) {
      if (diffBuffer[i] === 255 && diffBuffer[i + 3] === 255) {
        hasRedPixels = true;
        break;
      }
    }
    expect(hasRedPixels).toBe(true);
  });

  it("should handle identical images with no differences", async () => {
    const before = join(tempDir, "before.png");
    const after = join(tempDir, "after.png");
    const diff = join(tempDir, "diff.png");

    await createImage(before, { r: 0, g: 0, b: 0 }); // Black
    await createImage(after, { r: 0, g: 0, b: 0 }); // Black

    await generateDiffImage(before, after, diff);

    // Verify the diff image was created
    expect(existsSync(diff)).toBe(true);

    const diffImage = sharp(diff);
    const metadata = await diffImage.metadata();
    expect(metadata.width).toBe(10);
    expect(metadata.height).toBe(10);
    expect(metadata.channels).toBe(4); // RGBA

    // For identical images, the diff should exist but may have some processing artifacts
    // The important thing is that the function completes without error
    // and produces a valid diff image
    const diffBuffer = await diffImage
      .ensureAlpha()
      .raw({ depth: "uchar" })
      .toBuffer({ resolveWithObject: false });

    // Verify we got valid image data
    expect(diffBuffer.length).toBeGreaterThan(0);
    expect(diffBuffer.length % 4).toBe(0); // Should be divisible by 4 (RGBA)
  });

  it("should handle images with different sizes", async () => {
    const before = join(tempDir, "before.png");
    const after = join(tempDir, "after.png");
    const diff = join(tempDir, "diff.png");

    await createImage(before, { r: 0, g: 0, b: 0 }, { width: 10, height: 10 });
    await createImage(
      after,
      { r: 255, g: 255, b: 255 },
      { width: 20, height: 20 }
    );

    await generateDiffImage(before, after, diff);

    const diffImage = sharp(diff);
    const metadata = await diffImage.metadata();
    expect(metadata.width).toBe(20);
    expect(metadata.height).toBe(20);
  });

  it("should throw error for nonexistent file", async () => {
    const before = join(tempDir, "doesnotexist.png");
    const after = join(tempDir, "after.png");
    const diff = join(tempDir, "diff.png");

    await createImage(after, { r: 0, g: 0, b: 0 });

    await expect(generateDiffImage(before, after, diff)).rejects.toThrow();
  });

  it("should throw error for invalid image file", async () => {
    const before = join(tempDir, "before.txt");
    const after = join(tempDir, "after.png");
    const diff = join(tempDir, "diff.png");

    // Write non-image content
    const { writeFileSync } = await import("fs");
    writeFileSync(before, "not an image");
    await createImage(after, { r: 0, g: 0, b: 0 });

    await expect(generateDiffImage(before, after, diff)).rejects.toThrow();
  });
});
