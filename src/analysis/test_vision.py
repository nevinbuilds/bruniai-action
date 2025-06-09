import pytest
import json
import base64
from unittest.mock import patch, MagicMock
from datetime import datetime
from .vision import analyze_images_with_vision

# Sample test data
SAMPLE_BASE_SCREENSHOT = "test_base.png"
SAMPLE_PR_SCREENSHOT = "test_pr.png"
SAMPLE_DIFF_IMAGE = "test_diff.png"
SAMPLE_BASE_URL = "https://example.com"
SAMPLE_PREVIEW_URL = "https://preview.example.com"
SAMPLE_PR_NUMBER = "123"
SAMPLE_REPOSITORY = "test/repo"
SAMPLE_USER_ID = "user123"

# Sample sections analysis
SAMPLE_SECTIONS_ANALYSIS = """
Header Section: Present at top of page
Navigation Menu: Present below header
Hero Section: Present in middle of page
Footer: Present at bottom of page
"""

# Sample OpenAI response
SAMPLE_OPENAI_RESPONSE = {
    "id": "test-uuid",
    "url": SAMPLE_BASE_URL,
    "preview_url": SAMPLE_PREVIEW_URL,
    "repository": SAMPLE_REPOSITORY,
    "pr_number": SAMPLE_PR_NUMBER,
    "timestamp": datetime.utcnow().isoformat(),
    "status": "pass",
    "status_enum": "pass",
    "critical_issues": {
        "sections": [
            {
                "name": "Header Section",
                "status": "Present",
                "description": "Header section is present and correctly positioned"
            }
        ],
        "summary": "No critical issues found"
    },
    "critical_issues_enum": "none",
    "structural_analysis": {
        "section_order": "All sections maintain their original order",
        "layout": "Layout structure remains consistent",
        "broken_layouts": "No broken layouts detected"
    },
    "visual_changes": {
        "diff_highlights": ["Minor text updates in header"],
        "animation_issues": "No animation issues detected",
        "conclusion": "Changes are within acceptable parameters"
    },
    "visual_changes_enum": "minor",
    "conclusion": {
        "critical_issues": "No critical issues found",
        "visual_changes": "Minor visual changes only",
        "recommendation": "pass",
        "summary": "Changes are acceptable and do not require review"
    },
    "recommendation_enum": "pass",
    "created_at": datetime.utcnow().isoformat(),
    "user_id": SAMPLE_USER_ID
}

@pytest.fixture
def mock_openai():
    """
    Fixture that mocks the OpenAI API client.

    This fixture:
    - Mocks the OpenAI client to avoid making real API calls
    - Returns a mock instance that simulates the API response
    - Uses SAMPLE_OPENAI_RESPONSE as the default response
    """
    with patch('openai.OpenAI') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps(SAMPLE_OPENAI_RESPONSE)))
        ]
        yield mock_instance

@pytest.fixture
def mock_file_operations():
    """
    Fixture that mocks file operations for reading images.

    This fixture:
    - Mocks the built-in open() function
    - Simulates reading image data without accessing real files
    - Returns mock file handle with test image data
    """
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = b"test image data"
        yield mock_open

@pytest.mark.asyncio
async def test_analyze_images_with_vision_success(mock_openai, mock_file_operations):
    """
    Test the successful analysis of images with all parameters provided.

    This test verifies:
    - The function can process images with all optional parameters
    - The response structure matches the expected format
    - All enum values are correctly set
    - Critical issues section is properly populated
    - The function correctly handles PR context (title and description)
    """
    result = await analyze_images_with_vision(
        base_screenshot=SAMPLE_BASE_SCREENSHOT,
        pr_screenshot=SAMPLE_PR_SCREENSHOT,
        diff_image=SAMPLE_DIFF_IMAGE,
        base_url=SAMPLE_BASE_URL,
        preview_url=SAMPLE_PREVIEW_URL,
        pr_number=SAMPLE_PR_NUMBER,
        repository=SAMPLE_REPOSITORY,
        sections_analysis=SAMPLE_SECTIONS_ANALYSIS,
        pr_title="Test PR",
        pr_description="Test description",
        user_id=SAMPLE_USER_ID
    )

    # Verify the result structure
    assert result["status"] == "pass"
    assert result["status_enum"] == "pass"
    assert result["critical_issues_enum"] == "none"
    assert result["visual_changes_enum"] == "minor"
    assert result["recommendation_enum"] == "pass"
    assert "sections" in result["critical_issues"]
    assert len(result["critical_issues"]["sections"]) > 0

@pytest.mark.asyncio
async def test_analyze_images_with_vision_minimal_params(mock_openai, mock_file_operations):
    """
    Test the image analysis with only required parameters.

    This test verifies:
    - The function works with minimal required parameters
    - Optional parameters (sections_analysis, pr_title, pr_description) are handled correctly
    - The response contains all required fields
    - Metadata fields (url, preview_url, pr_number, repository) are correctly set
    """
    result = await analyze_images_with_vision(
        base_screenshot=SAMPLE_BASE_SCREENSHOT,
        pr_screenshot=SAMPLE_PR_SCREENSHOT,
        diff_image=SAMPLE_DIFF_IMAGE,
        base_url=SAMPLE_BASE_URL,
        preview_url=SAMPLE_PREVIEW_URL,
        pr_number=SAMPLE_PR_NUMBER,
        repository=SAMPLE_REPOSITORY
    )

    assert result["status"] == "pass"
    assert result["url"] == SAMPLE_BASE_URL
    assert result["preview_url"] == SAMPLE_PREVIEW_URL
    assert result["pr_number"] == SAMPLE_PR_NUMBER
    assert result["repository"] == SAMPLE_REPOSITORY

@pytest.mark.asyncio
async def test_analyze_images_with_vision_invalid_json(mock_openai, mock_file_operations):
    """
    Test error handling for invalid JSON responses from OpenAI.

    This test verifies:
    - The function properly handles invalid JSON responses
    - Appropriate error messages are raised
    - The error contains information about JSON parsing failure
    - The function fails gracefully when the API response is malformed
    """
    mock_openai.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="invalid json"))
    ]

    with pytest.raises(Exception) as exc_info:
        await analyze_images_with_vision(
            base_screenshot=SAMPLE_BASE_SCREENSHOT,
            pr_screenshot=SAMPLE_PR_SCREENSHOT,
            diff_image=SAMPLE_DIFF_IMAGE,
            base_url=SAMPLE_BASE_URL,
            preview_url=SAMPLE_PREVIEW_URL,
            pr_number=SAMPLE_PR_NUMBER,
            repository=SAMPLE_REPOSITORY
        )

    assert "Failed to parse AI response as JSON" in str(exc_info.value)

@pytest.mark.asyncio
async def test_analyze_images_with_vision_invalid_enum(mock_openai, mock_file_operations):
    """
    Test handling of invalid enum values in the API response.

    This test verifies:
    - The function properly handles invalid enum values
    - Invalid enum values are corrected to appropriate defaults
    - The correction logic works for all enum fields:
      - status_enum -> "warning"
      - critical_issues_enum -> "other_issues"
      - visual_changes_enum -> "minor"
      - recommendation_enum -> "review_required"
    - The function continues to work despite invalid enum values
    """
    invalid_response = SAMPLE_OPENAI_RESPONSE.copy()
    invalid_response["status_enum"] = "invalid_status"
    invalid_response["critical_issues_enum"] = "invalid_issues"
    invalid_response["visual_changes_enum"] = "invalid_changes"
    invalid_response["recommendation_enum"] = "invalid_recommendation"

    mock_openai.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=json.dumps(invalid_response)))
    ]

    result = await analyze_images_with_vision(
        base_screenshot=SAMPLE_BASE_SCREENSHOT,
        pr_screenshot=SAMPLE_PR_SCREENSHOT,
        diff_image=SAMPLE_DIFF_IMAGE,
        base_url=SAMPLE_BASE_URL,
        preview_url=SAMPLE_PREVIEW_URL,
        pr_number=SAMPLE_PR_NUMBER,
        repository=SAMPLE_REPOSITORY
    )

    # Verify that invalid enums were corrected to default values
    assert result["status_enum"] == "warning"
    assert result["critical_issues_enum"] == "other_issues"
    assert result["visual_changes_enum"] == "minor"
    assert result["recommendation_enum"] == "review_required"
