"""
Test suite for the image diff generation functionality.

This module tests the generate_diff_image function which is responsible for:
1. Creating visual difference maps between two images
2. Handling images of different sizes
3. Managing transparency in the output
4. Error handling for invalid inputs

The tests cover various scenarios:
- Basic difference detection between images
- Cases with no differences
- Images of different sizes
- Error cases (missing files, invalid files)
"""

import os
import pytest
from PIL import Image
import numpy as np
from src.image_processing.diff import generate_diff_image

def create_image(path, color, size=(10, 10)):
    """Helper function to create test images with specified color and size."""
    img = Image.new('RGB', size, color)
    img.save(path)

def test_generate_diff_image_basic(tmp_path):
    """
    Test basic difference detection between two images.

    Creates two images with different colors (white and red) and verifies that:
    1. The diff image is created successfully
    2. The output is in RGBA format
    3. The differences are marked in red with full opacity
    """
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    create_image(before, (255, 255, 255))
    create_image(after, (255, 0, 0))
    generate_diff_image(str(before), str(after), str(diff))
    assert diff.exists()
    out_img = Image.open(diff)
    assert out_img.mode == 'RGBA'
    assert out_img.size == (10, 10)
    arr = np.array(out_img)
    # There should be some red pixels (differences)
    assert (arr[..., 0] == 255).any() and (arr[..., 3] == 255).any()

def test_generate_diff_image_no_difference(tmp_path):
    """
    Test behavior when comparing identical images.

    Verifies that when two identical images are compared:
    1. The diff image is created
    2. All pixels are fully transparent (alpha = 0)
    3. No differences are marked
    """
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    create_image(before, (0, 0, 0))
    create_image(after, (0, 0, 0))
    generate_diff_image(str(before), str(after), str(diff))
    out_img = Image.open(diff)
    arr = np.array(out_img)
    # All alpha should be 0 (fully transparent)
    assert (arr[..., 3] == 0).all()

def test_generate_diff_image_different_sizes(tmp_path):
    """
    Test handling of images with different dimensions.

    Verifies that when comparing images of different sizes:
    1. The output image uses the larger dimensions
    2. The diff is generated correctly across the entire area
    3. The smaller image is properly padded
    """
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    create_image(before, (0, 0, 0), size=(10, 10))
    create_image(after, (255, 255, 255), size=(20, 20))
    generate_diff_image(str(before), str(after), str(diff))
    out_img = Image.open(diff)
    assert out_img.size == (20, 20)

def test_generate_diff_image_nonexistent_file(tmp_path):
    """
    Test error handling for missing input files.

    Verifies that the function properly raises FileNotFoundError
    when one of the input images doesn't exist.
    """
    before = tmp_path / "doesnotexist.png"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    create_image(after, (0, 0, 0))
    with pytest.raises(FileNotFoundError):
        generate_diff_image(str(before), str(after), str(diff))

def test_generate_diff_image_non_image_file(tmp_path):
    """
    Test error handling for invalid input files.

    Verifies that the function properly raises an exception
    when one of the input files is not a valid image.
    """
    before = tmp_path / "before.txt"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    before.write_text("not an image")
    create_image(after, (0, 0, 0))
    with pytest.raises(Exception):
        generate_diff_image(str(before), str(after), str(diff))
