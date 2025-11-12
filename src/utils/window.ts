/**
 * Ensure viewport is set to 1920x1080 and verify it's correct.
 * Optionally navigate to a URL after setting the viewport.
 *
 * @param page - The page object from Stagehand
 * @param url - Optional URL to navigate to after setting viewport
 * @returns Promise that resolves when viewport is set and verified
 */
export async function ensureViewportSize(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  page: any,
  url?: string
): Promise<void> {
  // Set viewport size before navigating (if URL provided).
  page.setViewportSize(1920, 1080);

  // Navigate to URL if provided.
  if (url) {
    await page.goto(url);
  }

  // Verify viewport is set correctly.
  const viewportSize = await page.evaluate(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const win = (globalThis as any).window;
    return {
      width: win.innerWidth,
      height: win.innerHeight,
    };
  });

  // Reset viewport if it's 0 width (navigation may have reset it).
  if (viewportSize.width === 0) {
    console.warn(
      `Viewport width is 0 after navigation, resetting to 1920x1080`
    );
    page.setViewportSize(1920, 1080);
    // Wait a bit for viewport to be applied.
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
}
