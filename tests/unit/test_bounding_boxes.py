import pytest
from unittest.mock import AsyncMock, patch
from src.playwright_utils.bounding_boxes import extract_section_bounding_boxes

@pytest.mark.asyncio
async def test_extract_section_bounding_boxes_error_handling():
    """
    Test the error handling behavior of extract_section_bounding_boxes when network errors occur.

    This test verifies that the function gracefully handles network errors during browser launch
    by returning an empty list instead of propagating the exception. This is important for:
    1. Ensuring the visual testing pipeline continues even when network issues occur
    2. Preventing cascading failures in the testing system
    3. Maintaining a consistent return type (list) even in error cases
    """
    # Create a mock Playwright instance that will simulate a network error
    # This simulates what would happen if the browser couldn't be launched due to network issues
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.side_effect = Exception("Network error")

    # Patch the Playwright import to use our mock instead of the real Playwright
    # This allows us to test the error handling without actually launching a browser
    with patch("playwright.async_api.async_playwright", return_value=mock_playwright):
        # Call the function with a test URL
        # Even though we're using a real URL, the mock will prevent actual network calls
        result = await extract_section_bounding_boxes("https://example.com")
        # Verify that the function returns an empty list when network errors occur
        # This is the expected behavior for graceful error handling
        assert result == []
