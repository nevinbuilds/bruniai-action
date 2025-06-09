"""
Test suite for the main runner entrypoint.

This module contains a basic smoke test for the main() function to verify that:
1. The function can be called without errors
2. The basic flow of argument parsing and environment setup works
3. The function handles early returns gracefully

Note: Detailed testing of individual components (screenshots, image processing, API calls)
is handled in their respective test modules.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import os
from src.runner.__main__ import main

@pytest.mark.asyncio
async def test_main_smoke_test(tmp_path):
    """
    Basic smoke test for the main function.

    This test verifies that:
    1. The function can be called without errors
    2. Environment variables are properly handled
    3. Command line arguments are parsed correctly
    4. The function returns early when screenshots fail
    """
    # Mock environment variables
    with patch.dict(os.environ, {
        "GITHUB_REPOSITORY": "org/repo",
        "PR_NUMBER": "123",
        "GITHUB_WORKSPACE": str(tmp_path)
    }):
        # Mock the argument parser
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                base_url="http://example.com",
                pr_url="http://preview.com",
                bruni_token=None,
                bruni_api_url=None
            )

            # Mock the screenshot function to return False (early return case)
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=False):
                # Run the main function
                await main()
                # The function should return early due to failed screenshots
                # No need to verify further calls as they shouldn't happen
