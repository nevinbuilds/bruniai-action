import pytest
from datetime import datetime
from reporter.types import (
    ReportData,
    ReportStatus,
    CriticalIssuesStatus,
    VisualChangesStatus,
    RecommendationStatus
)
from reporter.report_generator import parse_analysis_results

def test_parse_analysis_results_default_structure():
    """Test that parse_analysis_results returns correct default structure."""
    report = parse_analysis_results(
        base_url="https://example.com",
        preview_url="https://preview.example.com",
        pr_number="123",
        repository="test/repo",
        visual_analysis={}
    )

    # Test required fields
    assert report["url"] == "https://example.com"
    assert report["preview_url"] == "https://preview.example.com"
    assert report["repository"] == "test/repo"
    assert report["pr_number"] == "123"
    assert isinstance(report["timestamp"], str)
    assert isinstance(report["id"], str)

    # Test default values
    assert report["status"] == "none"
    assert report["status_enum"] == "none"
    assert report["critical_issues_enum"] == "none"
    assert report["visual_changes_enum"] == "none"
    assert report["recommendation_enum"] == "pass"

    # Test nested structures
    assert isinstance(report["critical_issues"], dict)
    assert isinstance(report["critical_issues"]["sections"], list)
    assert isinstance(report["critical_issues"]["summary"], str)
    assert isinstance(report["structural_analysis"], dict)
    assert isinstance(report["visual_changes"], dict)
    assert isinstance(report["conclusion"], dict)

def test_parse_analysis_results_string_based():
    """Test parsing string-based analysis (backward compatibility)."""
    # Test missing sections
    report = parse_analysis_results(
        base_url="https://example.com",
        preview_url="https://preview.example.com",
        pr_number="123",
        repository="test/repo",
        visual_analysis="Found missing sections in the layout"
    )
    assert report["critical_issues_enum"] == "missing_sections"
    assert report["status"] == "fail"
    assert report["status_enum"] == "fail"

    # Test significant changes
    report = parse_analysis_results(
        base_url="https://example.com",
        preview_url="https://preview.example.com",
        pr_number="123",
        repository="test/repo",
        visual_analysis="Found significant changes in the layout"
    )
    assert report["visual_changes_enum"] == "significant"
    assert report["recommendation_enum"] == "review_required"
    assert report["status"] == "warning"
    assert report["status_enum"] == "warning"

    # Test minor changes
    report = parse_analysis_results(
        base_url="https://example.com",
        preview_url="https://preview.example.com",
        pr_number="123",
        repository="test/repo",
        visual_analysis="Found minor changes in the layout"
    )
    assert report["visual_changes_enum"] == "minor"
    assert report["status"] == "pass"
    assert report["status_enum"] == "pass"

def test_parse_analysis_results_structured():
    """Test parsing structured analysis data."""
    structured_data = {
        "status_enum": "warning",
        "critical_issues": {
            "sections": [
                {
                    "name": "Header",
                    "status": "missing",
                    "description": "Header section is missing"
                }
            ],
            "summary": "Missing critical sections"
        },
        "critical_issues_enum": "missing_sections",
        "structural_analysis": {
            "section_order": "invalid",
            "layout": "broken",
            "broken_layouts": "header, footer"
        },
        "visual_changes": {
            "diff_highlights": ["Color changes in header"],
            "animation_issues": "None",
            "conclusion": "Minor visual changes detected"
        },
        "visual_changes_enum": "minor",
        "conclusion": {
            "critical_issues": "Missing header section",
            "visual_changes": "Minor color changes",
            "recommendation": "review_required",
            "summary": "Review required due to missing sections"
        },
        "recommendation_enum": "review_required"
    }

    report = parse_analysis_results(
        base_url="https://example.com",
        preview_url="https://preview.example.com",
        pr_number="123",
        repository="test/repo",
        visual_analysis=structured_data
    )

    # Test status enums
    assert report["status_enum"] == "warning"
    assert report["critical_issues_enum"] == "missing_sections"
    assert report["visual_changes_enum"] == "minor"
    assert report["recommendation_enum"] == "review_required"

    # Test critical issues
    assert len(report["critical_issues"]["sections"]) == 1
    assert report["critical_issues"]["sections"][0]["name"] == "Header"
    assert report["critical_issues"]["summary"] == "Missing critical sections"

    # Test structural analysis
    assert report["structural_analysis"]["section_order"] == "invalid"
    assert report["structural_analysis"]["layout"] == "broken"
    assert report["structural_analysis"]["broken_layouts"] == "header, footer"

    # Test visual changes
    assert report["visual_changes"]["diff_highlights"] == ["Color changes in header"]
    assert report["visual_changes"]["conclusion"] == "Minor visual changes detected"

    # Test conclusion
    assert report["conclusion"]["critical_issues"] == "Missing header section"
    assert report["conclusion"]["recommendation"] == "review_required"
    assert report["conclusion"]["summary"] == "Review required due to missing sections"

def test_parse_analysis_results_error_handling():
    """Test error handling in parse_analysis_results."""
    # Test with invalid structured data
    invalid_data = {
        "status_enum": "invalid_status",  # Invalid status
        "critical_issues": "not a dict",  # Invalid type
        "visual_changes": None  # Missing required fields
    }

    report = parse_analysis_results(
        base_url="https://example.com",
        preview_url="https://preview.example.com",
        pr_number="123",
        repository="test/repo",
        visual_analysis=invalid_data
    )

    # Should handle errors gracefully and set appropriate status
    assert "Error parsing visual analysis" in report["conclusion"]["summary"]
    assert report["recommendation_enum"] == "review_required"
    assert report["status_enum"] == "fail"
    assert report["critical_issues_enum"] == "other_issues"

def test_parse_analysis_results_with_image_refs():
    """Test parsing analysis results with image references."""
    image_refs = {
        "base_screenshot": "base64_encoded_image_1",
        "pr_screenshot": "base64_encoded_image_2",
        "diff_image": "base64_encoded_image_3"
    }

    report = parse_analysis_results(
        base_url="https://example.com",
        preview_url="https://preview.example.com",
        pr_number="123",
        repository="test/repo",
        visual_analysis={},
        image_refs=image_refs
    )

    assert report["image_refs"] == image_refs
    assert report["image_refs"]["base_screenshot"] == "base64_encoded_image_1"
    assert report["image_refs"]["pr_screenshot"] == "base64_encoded_image_2"
    assert report["image_refs"]["diff_image"] == "base64_encoded_image_3"
