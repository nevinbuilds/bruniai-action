import sharp from "sharp";
import { readFileSync, existsSync } from "fs";
import { extname } from "path";

/**
 * Compress, resize, and base64-encode an image.
 *
 * Uses WebP format with quality settings to reduce payload size.
 * This is particularly useful for API requests with size limits.
 *
 * @param imagePath - Path to the image file.
 * @param targetFormat - Output format ('WEBP', 'JPEG', or 'PNG').
 * @param maxDim - Maximum dimension (width or height) in pixels.
 * @param quality - Compression quality (0-100, higher = better quality).
 * @returns Base64-encoded string of the compressed image.
 * @throws Error if the image file cannot be read.
 */
export async function encodeImageCompressed(
  imagePath: string,
  targetFormat: string = "WEBP",
  maxDim: number = 1200,
  quality: number = 60
): Promise<string> {
  try {
    // Prefer an existing resized image if available.
    const ext = extname(imagePath);
    const base = imagePath.replace(ext, "");
    const resizedPath = `${base}-resized${ext}`;
    const path = existsSync(resizedPath) ? resizedPath : imagePath;

    let img = sharp(path);
    const metadata = await img.metadata();

    // Convert RGBA/P to RGB for JPEG/WebP compatibility.
    if (metadata.hasAlpha || metadata.format === "png") {
      img = img.removeAlpha();
    }

    // Resize if image is too large.
    const width = metadata.width || 0;
    const height = metadata.height || 0;
    const longest = Math.max(width, height);

    if (longest > maxDim) {
      const scale = maxDim / longest;
      const newWidth = Math.round(width * scale);
      const newHeight = Math.round(height * scale);
      img = img.resize(newWidth, newHeight, {
        kernel: "lanczos3",
      });
    }

    // Compress and encode.
    const fmt = targetFormat.toUpperCase();
    let buffer: Buffer;

    if (fmt === "JPG" || fmt === "JPEG") {
      buffer = await img
        .jpeg({ quality, mozjpeg: true, progressive: true })
        .toBuffer();
    } else if (fmt === "WEBP") {
      buffer = await img.webp({ quality, effort: 6 }).toBuffer();
    } else {
      // Fallback to PNG if unknown format.
      buffer = await img.png({ compressionLevel: 9 }).toBuffer();
    }

    return buffer.toString("base64");
  } catch (error) {
    // Fallback to raw file bytes if compression fails.
    console.warn(
      `Failed to compress image ${imagePath}: ${error}. Using original.`
    );
    try {
      const imageBuffer = readFileSync(imagePath);
      return imageBuffer.toString("base64");
    } catch (fallbackError) {
      throw new Error(
        `Failed to read image file ${imagePath}: ${fallbackError}`
      );
    }
  }
}
