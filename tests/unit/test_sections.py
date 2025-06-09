import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.analysis.sections import analyze_sections_side_by_side

@pytest.mark.asyncio
async def test_analyze_sections_side_by_side_retries_on_timeout():
    # Patch Runner.run to always raise TimeoutError
    with patch("src.analysis.sections.Runner.run", new_callable=AsyncMock) as mock_run, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
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
