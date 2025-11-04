"""
Test suite for section analysis retry logic.

This module tests the analyze_sections_side_by_side function, ensuring:
1. The function retries on timeout errors up to the maximum allowed attempts
2. Proper error handling and retry delays are implemented
3. The function raises an exception after all retries are exhausted

The tests cover:
- Retry logic for timeouts
- Correct number of retries and sleep calls
- Exception raising after max retries
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.analysis.sections import analyze_sections_side_by_side

@pytest.mark.asyncio
async def test_analyze_sections_side_by_side_retries_on_timeout():
    # Mock extract_real_dom_info to avoid Playwright calls
    mock_dom_info = [{
        "tag": "section",
        "id": "hero",
        "className": "hero-section",
        "ariaLabel": "Hero section",
        "textContent": "Welcome",
        "boundingBox": {"x": 0, "y": 0, "width": 100, "height": 100}
    }]

    # Patch Runner.run to always raise TimeoutError
    with patch("src.analysis.sections.extract_real_dom_info", new_callable=AsyncMock) as mock_extract, \
         patch("src.analysis.sections.Runner.run", new_callable=AsyncMock) as mock_run, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_extract.return_value = mock_dom_info
        mock_run.side_effect = asyncio.TimeoutError
        mcp_server = "dummy_server"
        base_url = "http://example.com"
        preview_url = "http://preview.com"
        # Should raise after max retries
        with pytest.raises(Exception, match="Section analysis timed out after all retries"):
            await analyze_sections_side_by_side(mcp_server, base_url, preview_url)
        # Should have retried 3 times
        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2  # sleep is not called after the last attempt
