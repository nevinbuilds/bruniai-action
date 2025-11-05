import logging
import os
import base64
from PIL import Image
from io import BytesIO

logger = logging.getLogger("agent-runner")


def encode_image_compressed(
    image_path: str,
    target_format: str = 'WEBP',
    max_dim: int = 1200,
    quality: int = 60
) -> str:
    """
    Compress, resize, and base64-encode an image.

    Uses WebP format with quality settings to reduce payload size.
    This is particularly useful for API requests with size limits.

    Args:
        image_path: Path to the image file.
        target_format: Output format ('WEBP', 'JPEG', or 'PNG').
        max_dim: Maximum dimension (width or height) in pixels.
        quality: Compression quality (0-100, higher = better quality).

    Returns:
        Base64-encoded string of the compressed image.

    Raises:
        FileNotFoundError: If the image file doesn't exist (caught and logged).
    """
    try:
        # Prefer an existing resized image if available.
        base, ext = os.path.splitext(image_path)
        resized_path = f"{base}-resized{ext}"
        path = resized_path if os.path.exists(resized_path) else image_path

        img = Image.open(path)

        # Convert RGBA/P to RGB for JPEG/WebP compatibility.
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if image is too large.
        w, h = img.size
        longest = max(w, h)
        if longest > max_dim:
            scale = max_dim / float(longest)
            new_w = int(w * scale)
            new_h = int(h * scale)
            # Use Resampling.LANCZOS if available, fallback to LANCZOS.
            try:
                resample = Image.Resampling.LANCZOS
            except AttributeError:
                resample = Image.LANCZOS
            img = img.resize((new_w, new_h), resample)

        # Compress and encode.
        buf = BytesIO()
        fmt = target_format.upper()

        if fmt in ('JPG', 'JPEG'):
            img.save(buf, format='JPEG', quality=quality, optimize=True, progressive=True)
        elif fmt == 'WEBP':
            img.save(buf, format='WEBP', quality=quality, method=6)
        else:
            # Fallback to PNG if unknown format.
            img.save(buf, format='PNG', optimize=True)

        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        # Fallback to raw file bytes if compression fails.
        logger.warning(f"Failed to compress image {image_path}: {e}. Using original.")
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as fallback_error:
            logger.error(f"Failed to read image file {image_path}: {fallback_error}")
            raise

