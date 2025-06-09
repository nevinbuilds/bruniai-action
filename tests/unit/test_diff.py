import os
import pytest
from PIL import Image
import numpy as np
from src.image_processing.diff import generate_diff_image

def create_image(path, color, size=(10, 10)):
    img = Image.new('RGB', size, color)
    img.save(path)

def test_generate_diff_image_basic(tmp_path):
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
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    create_image(before, (0, 0, 0), size=(10, 10))
    create_image(after, (255, 255, 255), size=(20, 20))
    generate_diff_image(str(before), str(after), str(diff))
    out_img = Image.open(diff)
    assert out_img.size == (20, 20)

def test_generate_diff_image_nonexistent_file(tmp_path):
    before = tmp_path / "doesnotexist.png"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    create_image(after, (0, 0, 0))
    with pytest.raises(FileNotFoundError):
        generate_diff_image(str(before), str(after), str(diff))

def test_generate_diff_image_non_image_file(tmp_path):
    before = tmp_path / "before.txt"
    after = tmp_path / "after.png"
    diff = tmp_path / "diff.png"
    before.write_text("not an image")
    create_image(after, (0, 0, 0))
    with pytest.raises(Exception):
        generate_diff_image(str(before), str(after), str(diff))
