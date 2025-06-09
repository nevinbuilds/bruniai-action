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
    ImageReferences,
    ReportData
)

def test_report_status_values():
    """Test that ReportStatus only accepts valid values."""
    valid_statuses = ['pass', 'fail', 'warning', 'none']
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
        description="Test Description"
    )
    assert section["name"] == "Test Section"
    assert section["status"] == "pass"
    assert section["description"] == "Test Description"

    # Test with missing fields (should work but be incomplete)
    incomplete_section = SectionInfo({})
    assert "name" not in incomplete_section
    assert "status" not in incomplete_section
    assert "description" not in incomplete_section

def test_critical_issues_structure():
    """Test CriticalIssues structure."""
    # Test with all fields
    issues = CriticalIssues(
        sections=[
            SectionInfo(
                name="Test Section",
                status="pass",
                description="Test Description"
            )
        ],
        summary="Test Summary"
    )
    assert len(issues["sections"]) == 1
    assert issues["summary"] == "Test Summary"

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

def test_report_data_structure():
    """Test ReportData structure."""
    # Test with all required fields
    report = ReportData(
        url="https://example.com",
        preview_url="https://preview.example.com",
        repository="test/repo",
        pr_number="123",
        timestamp="2024-03-20T00:00:00Z",
        status="pass",
        critical_issues=CriticalIssues(
            sections=[],
            summary="No issues"
        ),
        structural_analysis=StructuralAnalysis(
            section_order="valid",
            layout="valid",
            broken_layouts="none"
        ),
        visual_changes=VisualChanges(
            diff_highlights=[],
            animation_issues="none",
            conclusion="No visual changes"
        ),
        conclusion=Conclusion(
            critical_issues="No critical issues",
            visual_changes="No visual changes",
            recommendation="Pass",
            summary="All good"
        )
    )

    # Test required fields
    assert report["url"] == "https://example.com"
    assert report["preview_url"] == "https://preview.example.com"
    assert report["repository"] == "test/repo"
    assert report["pr_number"] == "123"

    # Test optional fields
    assert report.get("id") is None
    assert report.get("created_at") is None
    assert report.get("user_id") is None
    assert report.get("image_refs") is None

    # Test with missing fields (should work but be incomplete)
    incomplete_report = ReportData({})
    assert "url" not in incomplete_report
    assert "preview_url" not in incomplete_report
    assert "repository" not in incomplete_report
    assert "pr_number" not in incomplete_report
