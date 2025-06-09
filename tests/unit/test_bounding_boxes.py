import pytest
from unittest.mock import AsyncMock, patch
from src.playwright_utils.bounding_boxes import extract_section_bounding_boxes

@pytest.mark.asyncio
async def test_extract_section_bounding_boxes_error_handling():
    # Mock Playwright to raise an exception
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.side_effect = Exception("Network error")

    with patch("playwright.async_api.async_playwright", return_value=mock_playwright):
        result = await extract_section_bounding_boxes("https://example.com")
        assert result == []
