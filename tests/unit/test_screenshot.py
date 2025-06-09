import os
import pytest
from unittest.mock import patch
from src.playwright_utils.screenshot import take_screenshot_with_playwright
import subprocess

def test_take_screenshot_with_playwright_success(tmp_path):
    output_path = tmp_path / "screenshot.png"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        # Simulate file creation
        with open(output_path, "w") as f:
            f.write("dummy content")
        assert take_screenshot_with_playwright("https://example.com", str(output_path)) is True
        assert output_path.exists()
        mock_run.assert_called_once()

def test_take_screenshot_with_playwright_subprocess_error(tmp_path):
    output_path = tmp_path / "screenshot.png"
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "npx", stderr="Playwright not found")
        assert take_screenshot_with_playwright("https://example.com", str(output_path)) is False
        assert not output_path.exists()

def test_take_screenshot_with_playwright_unexpected_error(tmp_path):
    output_path = tmp_path / "screenshot.png"
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Unexpected error")
        assert take_screenshot_with_playwright("https://example.com", str(output_path)) is False
        assert not output_path.exists()
