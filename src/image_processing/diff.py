import logging
from PIL import Image, ImageChops
import numpy as np

logger = logging.getLogger("agent-runner")

def generate_diff_image(before_path, after_path, diff_output_path):
    # Process only local files
    img1 = Image.open(before_path).convert('RGB')
    img2 = Image.open(after_path).convert('RGB')

    # Instead of resizing, create new white images with maximum dimensions
    max_width = max(img1.size[0], img2.size[0])
    max_height = max(img1.size[1], img2.size[1])

    # Create white background images
    new_img1 = Image.new('RGB', (max_width, max_height), 'white')
    new_img2 = Image.new('RGB', (max_width, max_height), 'white')

    # Paste original images onto white backgrounds (this will preserve their original sizes)
    new_img1.paste(img1, (0, 0))
    new_img2.paste(img2, (0, 0))

    # Save transformed images.
    new_img1.save(before_path.replace('.png', '-resized.png'))
    new_img2.save(after_path.replace('.png', '-resized.png'))

    # Create a diff image
    diff = ImageChops.difference(new_img1, new_img2)

    # Create a mask of non-zero differences
    diff_np = np.array(diff)
    mask = (diff_np != 0).any(axis=2)

    # Convert mask to RGBA format for transparency
    result_np = np.zeros((max_height, max_width, 4), dtype=np.uint8)

    # Set red color with full opacity where differences exist
    result_np[mask, 0] = 255  # R channel
    result_np[mask, 3] = 255  # Alpha channel (fully opaque)

    # Create final image from numpy array
    diff_highlight = Image.fromarray(result_np, 'RGBA')

    # Save the result as PNG to preserve transparency
    diff_highlight.save(diff_output_path, format='PNG')
    logger.info(f"Diff image saved at: {diff_output_path}")
