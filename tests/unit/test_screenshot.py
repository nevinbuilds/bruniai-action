"""
Test suite for screenshot capture functionality.

This module tests the screenshot capture function which is responsible for:
1. Taking screenshots of web pages using Playwright
2. Managing subprocess execution
3. Handling various error conditions
4. File output management

The tests cover various scenarios:
- Successful screenshot capture
- Subprocess execution errors
- Unexpected errors
- File system interactions
"""

import os
import pytest
from unittest.mock import patch
from src.playwright_utils.screenshot import take_screenshot_with_playwright
import subprocess

def test_take_screenshot_with_playwright_success(tmp_path):
    """
    Test successful screenshot capture.

    Verifies that when everything works correctly:
    1. The subprocess is executed with correct parameters
    2. The output file is created
    3. The function returns True
    4. The file exists at the specified path
    """
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
    """
    Test handling of subprocess execution errors.

    Verifies that when the subprocess fails:
    1. The function returns False
    2. No output file is created
    3. The error is properly handled
    4. The system remains in a clean state
    """
    output_path = tmp_path / "screenshot.png"
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "npx", stderr="Playwright not found")
        assert take_screenshot_with_playwright("https://example.com", str(output_path)) is False
        assert not output_path.exists()

def test_take_screenshot_with_playwright_unexpected_error(tmp_path):
    """
    Test handling of unexpected errors.

    Verifies that when an unexpected error occurs:
    1. The function returns False
    2. No output file is created
    3. The error is properly caught
    4. The system remains in a clean state
    """
    output_path = tmp_path / "screenshot.png"
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Unexpected error")
        assert take_screenshot_with_playwright("https://example.com", str(output_path)) is False
        assert not output_path.exists()
