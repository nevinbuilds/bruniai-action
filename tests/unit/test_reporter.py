"""
Test suite for BruniReporter class.

This module tests the BruniReporter.send_multi_page_report method, ensuring:
1. Proper chunking of large reports
2. Multiple API calls for chunks
3. Correct handling of responses from each chunk
4. Error handling for failed requests
5. Token validation
6. Response parsing (JSON and text fallback)

The tests cover:
- Single chunk scenarios
- Multiple chunk scenarios with large datasets
- Error handling for network issues
- Response parsing for different content types
- Token validation
- Edge cases with empty or invalid data
"""

import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from reporter.reporter import BruniReporter
from reporter.types import MultiPageReportData, PageReport, TestData, CriticalIssues, StructuralAnalysis, VisualChanges, Conclusion, ImageReferences


def create_sample_page_report(page_path: str = "/", status: str = "pass") -> PageReport:
    """Create a sample page report for testing."""
    return {
        "page_path": page_path,
        "url": f"https://example.com{page_path}",
        "preview_url": f"https://preview.example.com{page_path}",
        "status": status,
        "critical_issues": {
            "sections": [],
            "summary": ""
        },
        "structural_analysis": {
            "section_order": "",
            "layout": "",
            "broken_layouts": ""
        },
        "visual_changes": {
            "diff_highlights": [],
            "animation_issues": "",
            "conclusion": ""
        },
        "conclusion": {
            "critical_issues": "",
            "visual_changes": "",
            "recommendation": "",
            "summary": ""
        },
        "image_refs": None
    }


def create_multi_page_report_data(num_reports: int = 1) -> MultiPageReportData:
    """Create a multi-page report data structure for testing."""
    return {
        "test_data": {
            "pr_number": "123",
            "repository": "test/repo",
            "timestamp": datetime.now().isoformat()
        },
        "reports": [create_sample_page_report(f"/page{i}") for i in range(num_reports)]
    }


class MockClientSession:
    """Mock aiohttp.ClientSession that properly handles async context managers."""

    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    def __call__(self, *args, **kwargs):
        """Make the class callable like aiohttp.ClientSession()."""
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def post(self, *args, **kwargs):
        """Return a mock response context manager."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return MockResponseContext(response)


class MockResponseContext:
    """Mock response context manager."""

    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_send_multi_page_report_single_chunk():
    """Test sending a multi-page report that fits in a single chunk."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")
    report_data = create_multi_page_report_data(1)  # 1 report = 1 chunk

    mock_response = AsyncMock()
    mock_response.ok = True
    mock_response.status = 200
    mock_response.json.return_value = {"status": "success", "message": "Report received"}

    with patch('aiohttp.ClientSession', MockClientSession([mock_response])):
        result = await reporter.send_multi_page_report(report_data)

    assert result == [{"status": "success", "message": "Report received"}]


@pytest.mark.asyncio
async def test_send_multi_page_report_multiple_chunks():
    """Test sending a multi-page report that requires multiple chunks."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")

    # Create a report with 3 pages - should create 3 chunks (1 report per chunk)
    large_report_data = create_multi_page_report_data(3)

    mock_response1 = AsyncMock()
    mock_response1.ok = True
    mock_response1.status = 200
    mock_response1.json.return_value = {"status": "success", "chunk": 1}

    mock_response2 = AsyncMock()
    mock_response2.ok = True
    mock_response2.status = 200
    mock_response2.json.return_value = {"status": "success", "chunk": 2}

    mock_response3 = AsyncMock()
    mock_response3.ok = True
    mock_response3.status = 200
    mock_response3.json.return_value = {"status": "success", "chunk": 3}

    with patch('aiohttp.ClientSession', MockClientSession([mock_response1, mock_response2, mock_response3])):
        result = await reporter.send_multi_page_report(large_report_data)

    assert result == [
        {"status": "success", "chunk": 1},
        {"status": "success", "chunk": 2},
        {"status": "success", "chunk": 3}
    ]


@pytest.mark.asyncio
async def test_send_multi_page_report_no_token():
    """Test that the method returns None when no token is provided."""
    reporter = BruniReporter("", "https://api.bruni.com/reports")
    report_data = create_multi_page_report_data(1)

    result = await reporter.send_multi_page_report(report_data)

    assert result is None


@pytest.mark.asyncio
async def test_send_multi_page_report_api_error():
    """Test handling of API errors."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")
    report_data = create_multi_page_report_data(1)

    mock_response = AsyncMock()
    mock_response.ok = False
    mock_response.status = 500
    mock_response.text.return_value = "Internal Server Error"

    with patch('aiohttp.ClientSession', MockClientSession([mock_response])):
        with pytest.raises(ValueError, match="Failed to send multi-page report: 500 - Internal Server Error"):
            await reporter.send_multi_page_report(report_data)


@pytest.mark.asyncio
async def test_send_multi_page_report_network_error():
    """Test handling of network errors."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")
    report_data = create_multi_page_report_data(1)

    # Create a mock session that raises an error
    class MockErrorSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def post(self, *args, **kwargs):
            raise aiohttp.ClientError("Connection failed")

    with patch('aiohttp.ClientSession', MockErrorSession):
        with pytest.raises(aiohttp.ClientError, match="Connection failed"):
            await reporter.send_multi_page_report(report_data)


@pytest.mark.asyncio
async def test_send_multi_page_report_text_response():
    """Test handling of non-JSON responses."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")
    report_data = create_multi_page_report_data(1)

    mock_response = AsyncMock()
    mock_response.ok = True
    mock_response.status = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.text.return_value = "Success message"

    with patch('aiohttp.ClientSession', MockClientSession([mock_response])):
        result = await reporter.send_multi_page_report(report_data)

    assert result == [{"message": "Success message"}]


@pytest.mark.asyncio
async def test_send_multi_page_report_multiple_chunks_with_errors():
    """Test handling of errors in multi-chunk scenarios."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")

    # Create a report with 3 pages - should create 3 chunks
    large_report_data = create_multi_page_report_data(3)

    mock_response1 = AsyncMock()
    mock_response1.ok = True
    mock_response1.status = 200
    mock_response1.json.return_value = {"status": "success", "chunk": 1}

    mock_response2 = AsyncMock()
    mock_response2.ok = False
    mock_response2.status = 500
    mock_response2.text.return_value = "Server Error"

    with patch('aiohttp.ClientSession', MockClientSession([mock_response1, mock_response2])):
        with pytest.raises(ValueError, match="Failed to send multi-page report: 500 - Server Error"):
            await reporter.send_multi_page_report(large_report_data)


@pytest.mark.asyncio
async def test_send_multi_page_report_empty_reports():
    """Test handling of empty reports list."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")
    report_data = create_multi_page_report_data(0)  # Empty reports list

    mock_response = AsyncMock()
    mock_response.ok = True
    mock_response.status = 200
    mock_response.json.return_value = {"status": "success", "message": "No reports to process"}

    with patch('aiohttp.ClientSession', MockClientSession([mock_response])):
        result = await reporter.send_multi_page_report(report_data)

    assert result == []


@pytest.mark.asyncio
async def test_send_multi_page_report_chunk_size_boundary():
    """Test chunking behavior at the boundary of chunk size."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")

    # Create reports that are exactly at the chunk size boundary
    # With max_chunk_size = 1, each report is its own chunk
    boundary_report_data = create_multi_page_report_data(2)  # 2 reports = 2 chunks

    mock_response1 = AsyncMock()
    mock_response1.ok = True
    mock_response1.status = 200
    mock_response1.json.return_value = {"status": "success", "chunk": 1}

    mock_response2 = AsyncMock()
    mock_response2.ok = True
    mock_response2.status = 200
    mock_response2.json.return_value = {"status": "success", "chunk": 2}

    with patch('aiohttp.ClientSession', MockClientSession([mock_response1, mock_response2])):
        result = await reporter.send_multi_page_report(boundary_report_data)

    assert result == [
        {"status": "success", "chunk": 1},
        {"status": "success", "chunk": 2}
    ]


@pytest.mark.asyncio
async def test_send_multi_page_report_very_large_dataset():
    """Test handling of very large datasets requiring many chunks."""
    reporter = BruniReporter("test-token", "https://api.bruni.com/reports")

    # Create a dataset with 5 reports = 5 chunks
    large_dataset = create_multi_page_report_data(5)

    mock_responses = []
    for i in range(5):  # 5 chunks expected
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.status = 200
        mock_response.json.return_value = {"status": "success", "chunk": i + 1}
        mock_responses.append(mock_response)

    with patch('aiohttp.ClientSession', MockClientSession(mock_responses)):
        result = await reporter.send_multi_page_report(large_dataset)

    expected_results = [
        {"status": "success", "chunk": 1},
        {"status": "success", "chunk": 2},
        {"status": "success", "chunk": 3},
        {"status": "success", "chunk": 4},
        {"status": "success", "chunk": 5}
    ]
    assert result == expected_results
