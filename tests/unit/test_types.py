"""
Test suite for report data type definitions and validation.

This module tests the TypedDict and Literal types used for reporting and analysis, ensuring:
1. Only valid enum values are accepted for status fields
2. Data structures (SectionInfo, CriticalIssues, etc.) have the correct required and optional fields

The tests cover:
- Enum value validation for all status types
- Structure and field presence for all report-related TypedDicts
- Optional and required field handling
"""

import pytest
from reporter.types import (
    ReportStatus,
    CriticalIssuesStatus,
    VisualChangesStatus,
    RecommendationStatus,
    SectionInfo,
    CriticalIssues,
    StructuralAnalysis,
    VisualChanges,
    Conclusion,
    ImageReferences
)

def test_report_status_values():
    """Test that ReportStatus only accepts valid values."""
    valid_statuses = ['pass', 'fail', 'warning']
    for status in valid_statuses:
        assert status in ReportStatus.__args__

def test_critical_issues_status_values():
    """Test that CriticalIssuesStatus only accepts valid values."""
    valid_statuses = ['none', 'missing_sections', 'other_issues']
    for status in valid_statuses:
        assert status in CriticalIssuesStatus.__args__

def test_visual_changes_status_values():
    """Test that VisualChangesStatus only accepts valid values."""
    valid_statuses = ['none', 'minor', 'significant']
    for status in valid_statuses:
        assert status in VisualChangesStatus.__args__

def test_recommendation_status_values():
    """Test that RecommendationStatus only accepts valid values."""
    valid_statuses = ['pass', 'review_required', 'reject']
    for status in valid_statuses:
        assert status in RecommendationStatus.__args__

def test_section_info_structure():
    """Test SectionInfo structure."""
    # Test with all fields
    section = SectionInfo(
        name="Test Section",
        status="pass",
        description="Test Description",
        section_id="test-section-id"
    )
    assert section["name"] == "Test Section"
    assert section["status"] == "pass"
    assert section["description"] == "Test Description"
    assert section["section_id"] == "test-section-id"

    # Test with missing fields (should work but be incomplete)
    incomplete_section = SectionInfo({})
    assert "name" not in incomplete_section
    assert "status" not in incomplete_section
    assert "description" not in incomplete_section
    assert "section_id" not in incomplete_section
def test_critical_issues_structure():
    """Test CriticalIssues structure."""
    # Test with all fields
    issues = CriticalIssues(
        sections=[
            SectionInfo(
                name="Test Section",
                status="pass",
                description="Test Description",
                section_id="test-section-id"
            )
        ],
        summary="Test Summary"
    )
    assert len(issues["sections"]) == 1
    assert issues["summary"] == "Test Summary"
    assert issues["sections"][0]["section_id"] == "test-section-id"
    # Test with missing fields (should work but be incomplete)
    incomplete_issues = CriticalIssues({})
    assert "sections" not in incomplete_issues
    assert "summary" not in incomplete_issues

def test_image_references_optional_fields():
    """Test that ImageReferences fields are optional."""
    refs = ImageReferences()
    assert refs.get("base_screenshot") is None
    assert refs.get("pr_screenshot") is None
    assert refs.get("diff_image") is None
