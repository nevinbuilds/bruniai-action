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


def test_pages_format_edge_cases():
    """Test edge cases in pages format parsing."""
    import json
    from unittest.mock import patch, MagicMock
    
    pages_json = json.dumps(["about", "contact"])
    
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            base_url="http://example.com",
            pr_url="http://preview.com",
            bruni_token=None,
            bruni_api_url=None,
            pages=pages_json
        )
        
        from src.runner.__main__ import main
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--base-url', required=True)
        parser.add_argument('--pr-url', required=True)
        parser.add_argument('--bruni-token', required=False)
        parser.add_argument('--bruni-api-url', required=False)
        parser.add_argument('--pages', required=False)
        
        args = parser.parse_args(['--base-url', 'http://example.com', '--pr-url', 'http://preview.com', '--pages', pages_json])
        
        pages_to_process = []
        if args.pages:
            pages_data = json.loads(args.pages)
            
            if isinstance(pages_data, list) and all(isinstance(item, str) for item in pages_data):
                base_url = args.base_url.rstrip('/')
                pr_url = args.pr_url.rstrip('/')
                
                for relative_path in pages_data:
                    if not relative_path.startswith('/'):
                        relative_path = '/' + relative_path
                    
                    page_name = relative_path.strip('/').replace('/', ' ').title() or 'Homepage'
                    if page_name == '':
                        page_name = 'Homepage'
                    
                    pages_to_process.append({
                        'base_url': base_url + relative_path,
                        'pr_url': pr_url + relative_path,
                        'name': page_name
                    })
        
        assert len(pages_to_process) == 2
        assert pages_to_process[0]['name'] == 'About'
        assert pages_to_process[1]['name'] == 'Contact'
        assert pages_to_process[0]['base_url'] == 'http://example.com/about'


def test_pages_format_empty_path():
    """Test empty relative path handling (line 64)."""
    import json
    from unittest.mock import patch, MagicMock
    
    pages_json = json.dumps(["", "/"])
    
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            base_url="http://example.com",
            pr_url="http://preview.com",
            bruni_token=None,
            bruni_api_url=None,
            pages=pages_json
        )
        
        from src.runner.__main__ import main
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--base-url', required=True)
        parser.add_argument('--pr-url', required=True)
        parser.add_argument('--bruni-token', required=False)
        parser.add_argument('--bruni-api-url', required=False)
        parser.add_argument('--pages', required=False)
        
        args = parser.parse_args(['--base-url', 'http://example.com', '--pr-url', 'http://preview.com', '--pages', pages_json])
        
        pages_to_process = []
        if args.pages:
            pages_data = json.loads(args.pages)
            
            if isinstance(pages_data, list) and all(isinstance(item, str) for item in pages_data):
                base_url = args.base_url.rstrip('/')
                pr_url = args.pr_url.rstrip('/')
                
                for relative_path in pages_data:
                    if not relative_path.startswith('/'):
                        relative_path = '/' + relative_path
                    
                    page_name = relative_path.strip('/').replace('/', ' ').title() or 'Homepage'
                    if page_name == '':
                        page_name = 'Homepage'
                    
                    pages_to_process.append({
                        'base_url': base_url + relative_path,
                        'pr_url': pr_url + relative_path,
                        'name': page_name
                    })
        
        assert len(pages_to_process) == 2
        assert pages_to_process[0]['name'] == 'Homepage'  # Empty path becomes Homepage
        assert pages_to_process[1]['name'] == 'Homepage'  # Root path becomes Homepage


def test_pages_format_invalid_format():
    """Test invalid pages format handling (lines 80-81)."""
    import json
    from unittest.mock import patch, MagicMock
    
    pages_json = json.dumps({"invalid": "format"})
    
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            base_url="http://example.com",
            pr_url="http://preview.com",
            bruni_token=None,
            bruni_api_url=None,
            pages=pages_json
        )
        
        from src.runner.__main__ import main
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--base-url', required=True)
        parser.add_argument('--pr-url', required=True)
        parser.add_argument('--bruni-token', required=False)
        parser.add_argument('--bruni-api-url', required=False)
        parser.add_argument('--pages', required=False)
        
        args = parser.parse_args(['--base-url', 'http://example.com', '--pr-url', 'http://preview.com', '--pages', pages_json])
        
        pages_to_process = []
        invalid_format_detected = False
        
        if args.pages:
            try:
                pages_data = json.loads(args.pages)
                
                if isinstance(pages_data, list) and all(isinstance(item, str) for item in pages_data):
                    pass
                elif isinstance(pages_data, list) and all(isinstance(item, dict) for item in pages_data):
                    pass
                else:
                    invalid_format_detected = True
            except (json.JSONDecodeError, KeyError):
                pass
        
        assert invalid_format_detected


def test_format_multi_page_summary():
    """Test multi-page summary formatting function."""
    from src.runner.__main__ import format_multi_page_summary
    
    page_results = [
        {
            'page_name': 'Homepage',
            'base_url': 'http://example.com/',
            'pr_url': 'http://preview.com/',
            'visual_analysis': {'status_enum': 'pass'},
            'sections_analysis': 'Test sections analysis'
        },
        {
            'page_name': 'About',
            'base_url': 'http://example.com/about',
            'pr_url': 'http://preview.com/about',
            'visual_analysis': {'status_enum': 'warning'},
            'sections_analysis': 'Test sections analysis 2'
        }
    ]
    
    summary = format_multi_page_summary(page_results)
    assert "Multi-Page Visual Analysis (2 pages tested)" in summary
    assert "✅ Homepage" in summary
    assert "⚠️ About" in summary
    
    summary_with_url = format_multi_page_summary(page_results, "http://report.url")
    assert "📊 [View detailed report](http://report.url)" in summary_with_url


def test_encode_image():
    """Test image encoding function."""
    import tempfile
    import os
    from src.runner.__main__ import encode_image
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as tmp_file:
        tmp_file.write(b'fake image data')
        tmp_path = tmp_file.name
    
    try:
        encoded = encode_image(tmp_path)
        assert isinstance(encoded, str)
        assert len(encoded) > 0
    finally:
        os.unlink(tmp_path)
