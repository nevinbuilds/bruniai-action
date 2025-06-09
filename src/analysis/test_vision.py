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
    with patch('openai.OpenAI') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps(SAMPLE_OPENAI_RESPONSE)))
        ]
        yield mock_instance

@pytest.fixture
def mock_file_operations():
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = b"test image data"
        yield mock_open

@pytest.mark.asyncio
async def test_analyze_images_with_vision_success(mock_openai, mock_file_operations):
    """Test successful image analysis with all parameters"""
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
    """Test image analysis with minimal required parameters"""
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
    """Test handling of invalid JSON response from OpenAI"""
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
    """Test handling of invalid enum values in response"""
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
