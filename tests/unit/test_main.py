"""
Test suite for the main runner entrypoint and integration logic.

This module tests the main() function and its integration with:
1. Argument parsing and environment variable management
2. Screenshot capture and error handling
3. Section and visual analysis orchestration
4. BruniReporter integration and error handling
5. Rate limit and exception handling

The tests cover:
- Successful end-to-end runs with all required arguments
- Early exits on failed screenshots
- BruniReporter usage and error handling
- Rate limit and generic error handling
- PR number extraction from event data
- Correct function call sequences and argument passing
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
import os
from src.runner.__main__ import main
from openai import RateLimitError

@pytest.mark.asyncio
async def test_main_with_required_args(tmp_path):
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

            # Mock the screenshot function
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=True):
                # Mock the MCP server context manager
                with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                    mock_mcp.return_value.__aenter__.return_value = "mcp_server"
                    # Mock the analysis functions
                    with patch("src.runner.__main__.analyze_sections_side_by_side", new_callable=AsyncMock) as mock_sections, \
                         patch("src.runner.__main__.analyze_images_with_vision", new_callable=AsyncMock) as mock_vision:
                        mock_sections.return_value = "sections analysis"
                        mock_vision.return_value = {"status": "pass"}

                        # Run the main function
                        await main()

                        # Verify the analysis functions were called
                        mock_sections.assert_called_once()
                        mock_vision.assert_called_once()

@pytest.mark.asyncio
async def test_main_with_failed_screenshots(tmp_path):
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

            # Mock the screenshot function to return False
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=False):
                # Run the main function
                await main()
                # The function should return early due to failed screenshots
                # No need to verify further calls as they shouldn't happen

@pytest.mark.asyncio
async def test_main_with_bruni_reporter(tmp_path):
    # Mock environment variables
    with patch.dict(os.environ, {
        "GITHUB_REPOSITORY": "org/repo",
        "PR_NUMBER": "123",
        "GITHUB_WORKSPACE": str(tmp_path),
        "BRUNI_TOKEN": "fake_token"
    }):
        # Mock the argument parser
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                base_url="http://example.com",
                pr_url="http://preview.com",
                bruni_token=None,
                bruni_api_url=None
            )

            # Mock the screenshot function
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=True):
                # Mock the MCP server context manager
                with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                    mock_mcp.return_value.__aenter__.return_value = "mcp_server"
                    # Mock the analysis functions
                    with patch("src.runner.__main__.analyze_sections_side_by_side", new_callable=AsyncMock) as mock_sections, \
                         patch("src.runner.__main__.analyze_images_with_vision", new_callable=AsyncMock) as mock_vision, \
                         patch("src.runner.__main__.BruniReporter") as mock_reporter:
                        mock_sections.return_value = "sections analysis"
                        mock_vision.return_value = {"status": "pass"}
                        mock_reporter.return_value.send_report = AsyncMock(return_value={"id": "123"})

                        # Run the main function
                        await main()

                        # Verify the reporter was initialized and used
                        mock_reporter.assert_called_once()
                        mock_reporter.return_value.send_report.assert_called_once()

@pytest.mark.asyncio
async def test_main_with_rate_limit_error(tmp_path):
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

            # Mock the screenshot function
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=True):
                # Mock the MCP server context manager
                with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                    mock_mcp.return_value.__aenter__.return_value = "mcp_server"
                    # Mock the analysis functions to raise a generic Exception
                    with patch("src.runner.__main__.analyze_sections_side_by_side", new_callable=AsyncMock) as mock_sections:
                        mock_sections.side_effect = Exception("Rate limit exceeded")

                        # Run the main function
                        await main()
                        # The function should handle the rate limit error gracefully

@pytest.mark.asyncio
async def test_main_with_missing_pr_number(tmp_path):
    # Mock environment variables without PR_NUMBER
    with patch.dict(os.environ, {
        "GITHUB_REPOSITORY": "org/repo",
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

            # Mock get_pr_number_from_event to return a PR number
            with patch("src.runner.__main__.get_pr_number_from_event", return_value="456"):
                # Mock the screenshot function
                with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=True):
                    # Mock the MCP server context manager
                    with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                        mock_mcp.return_value.__aenter__.return_value = "mcp_server"
                        # Mock the analysis functions
                        with patch("src.runner.__main__.analyze_sections_side_by_side", new_callable=AsyncMock) as mock_sections, \
                             patch("src.runner.__main__.analyze_images_with_vision", new_callable=AsyncMock) as mock_vision:
                            mock_sections.return_value = "sections analysis"
                            mock_vision.return_value = {"status": "pass"}

                            # Run the main function
                            await main()

                            # Verify the analysis functions were called with the correct PR number
                            mock_vision.assert_called_once()
                            # Check that the PR number from get_pr_number_from_event was used (positional argument)
                            # pr_number is the 6th positional argument (index 5)
                            assert mock_vision.call_args[0][5] == "456"

@pytest.mark.asyncio
async def test_main_with_bruni_reporter_error(tmp_path):
    # Mock environment variables
    with patch.dict(os.environ, {
        "GITHUB_REPOSITORY": "org/repo",
        "PR_NUMBER": "123",
        "GITHUB_WORKSPACE": str(tmp_path),
        "BRUNI_TOKEN": "fake_token"
    }):
        # Mock the argument parser
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                base_url="http://example.com",
                pr_url="http://preview.com",
                bruni_token=None,
                bruni_api_url=None
            )

            # Mock the screenshot function
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=True):
                # Mock the MCP server context manager
                with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                    mock_mcp.return_value.__aenter__.return_value = "mcp_server"
                    # Mock the analysis functions
                    with patch("src.runner.__main__.analyze_sections_side_by_side", new_callable=AsyncMock) as mock_sections, \
                         patch("src.runner.__main__.analyze_images_with_vision", new_callable=AsyncMock) as mock_vision, \
                         patch("src.runner.__main__.BruniReporter") as mock_reporter:
                        mock_sections.return_value = "sections analysis"
                        mock_vision.return_value = {"status": "pass"}
                        # Make the reporter raise an exception
                        mock_reporter.return_value.send_report = AsyncMock(side_effect=Exception("API Error"))

                        # Run the main function
                        await main()

                        # Verify the reporter was initialized and used
                        mock_reporter.assert_called_once()
                        mock_reporter.return_value.send_report.assert_called_once()
                        # The function should continue despite the reporter error
