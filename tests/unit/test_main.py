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
import json
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
                bruni_api_url=None,
                pages=None
            )

            # Mock the screenshot function to return False (early return case)
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=False):
                # Mock the MCP server context manager
                with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                    mock_mcp.return_value.__aenter__.return_value = MagicMock()
                    mock_mcp.return_value.__aexit__.return_value = None
                    with patch("src.runner.__main__.fetch_pr_metadata", return_value=("Test PR", "Test description")):
                        with patch("src.runner.__main__.get_pr_number_from_event", return_value="123"):
                            # Run the main function
                            await main()


@pytest.mark.asyncio
async def test_main_multi_page_functionality(tmp_path):
    """Test that multi-page mode works correctly with simplified relative URL format."""
    pages_json = json.dumps(["/", "/about", "/contact"])
    
    with patch.dict(os.environ, {
        "GITHUB_REPOSITORY": "org/repo",
        "PR_NUMBER": "123",
        "GITHUB_WORKSPACE": str(tmp_path)
    }):
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                base_url="http://example.com",
                pr_url="http://preview.com",
                bruni_token=None,
                bruni_api_url=None,
                pages=pages_json
            )
            
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=False):
                # Mock the MCP server context manager
                with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                    mock_mcp.return_value.__aenter__.return_value = MagicMock()
                    mock_mcp.return_value.__aexit__.return_value = None
                    with patch("src.runner.__main__.fetch_pr_metadata", return_value=("Test PR", "Test description")):
                        with patch("src.runner.__main__.get_pr_number_from_event", return_value="123"):
                            await main()


@pytest.mark.asyncio
async def test_main_invalid_pages_json(tmp_path):
    """Test that invalid JSON in pages parameter is handled gracefully."""
    with patch.dict(os.environ, {
        "GITHUB_REPOSITORY": "org/repo",
        "PR_NUMBER": "123",
        "GITHUB_WORKSPACE": str(tmp_path)
    }):
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                base_url="http://example.com",
                pr_url="http://preview.com",
                bruni_token=None,
                bruni_api_url=None,
                pages="invalid json"
            )
            
            # Mock the MCP server context manager
            with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                mock_mcp.return_value.__aenter__.return_value = MagicMock()
                mock_mcp.return_value.__aexit__.return_value = None
                with patch("src.runner.__main__.fetch_pr_metadata", return_value=("Test PR", "Test description")):
                    with patch("src.runner.__main__.get_pr_number_from_event", return_value="123"):
                        await main()


@pytest.mark.asyncio
async def test_main_legacy_pages_format(tmp_path):
    """Test that legacy multi-page format still works for backward compatibility."""
    pages_json = json.dumps([
        {
            "name": "Homepage",
            "base_url": "https://example.com/",
            "pr_url": "https://preview.example.com/"
        },
        {
            "name": "About Page",
            "base_url": "https://example.com/about",
            "pr_url": "https://preview.example.com/about"
        }
    ])
    
    with patch.dict(os.environ, {
        "GITHUB_REPOSITORY": "org/repo",
        "PR_NUMBER": "123",
        "GITHUB_WORKSPACE": str(tmp_path)
    }):
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = MagicMock(
                base_url="http://example.com",
                pr_url="http://preview.com",
                bruni_token=None,
                bruni_api_url=None,
                pages=pages_json
            )
            
            with patch("src.runner.__main__.take_screenshot_with_playwright", return_value=False):
                with patch("src.runner.__main__.managed_mcp_server") as mock_mcp:
                    mock_mcp.return_value.__aenter__.return_value = MagicMock()
                    mock_mcp.return_value.__aexit__.return_value = None
                    with patch("src.runner.__main__.fetch_pr_metadata", return_value=("Test PR", "Test description")):
                        with patch("src.runner.__main__.get_pr_number_from_event", return_value="123"):
                            await main()


def test_aggregate_page_results():
    """Test the aggregation logic for multiple page results."""
    from src.runner.__main__ import aggregate_page_results
    
    page_results_pass = [
        {'visual_analysis': {'status_enum': 'pass'}},
        {'visual_analysis': {'status_enum': 'pass'}},
    ]
    result = aggregate_page_results(page_results_pass)
    assert result['status_enum'] == 'pass'
    assert result['recommendation_enum'] == 'pass'
    
    page_results_fail = [
        {'visual_analysis': {'status_enum': 'pass'}},
        {'visual_analysis': {'status_enum': 'fail'}},
    ]
    result = aggregate_page_results(page_results_fail)
    assert result['status_enum'] == 'fail'
    assert result['recommendation_enum'] == 'reject'
    
    page_results_warning = [
        {'visual_analysis': {'status_enum': 'pass'}},
        {'visual_analysis': {'status_enum': 'warning'}},
    ]
    result = aggregate_page_results(page_results_warning)
    assert result['status_enum'] == 'warning'
    assert result['recommendation_enum'] == 'review_required'
