"""
Test suite for multi-page report generation and analysis result parsing.

This module tests the parse_multi_page_analysis_results function, ensuring:
1. Correct multi-page report structure generation
2. Proper status determination for different scenarios
3. Handling of structured and string-based analysis
4. Image references integration
5. Edge cases and error handling

The tests cover:
- Multi-page report structure validation
- Status determination logic for critical issues, visual changes, and recommendations
- String-based analysis fallback
- Image references handling
- Edge cases with missing or invalid data
"""

import pytest
from datetime import datetime
from reporter.report_generator import parse_multi_page_analysis_results
from reporter.types import MultiPageReportData, PageReport, TestData

def test_parse_multi_page_analysis_results_basic_structure():
    """Test that parse_multi_page_analysis_results returns correct basic structure."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'No issues found'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    # Test test_data structure
    assert isinstance(result, dict)
    assert result["test_data"]["pr_number"] == "123"
    assert result["test_data"]["repository"] == "test/repo"
    assert isinstance(result["test_data"]["timestamp"], str)

    # Test reports structure
    assert len(result["reports"]) == 1
    report = result["reports"][0]
    assert report["page_path"] == "/"
    assert report["url"] == "https://example.com"
    assert report["preview_url"] == "https://preview.example.com"
    assert report["status"] == "pass"

def test_parse_multi_page_analysis_results_critical_issues():
    """Test status determination when critical issues are present."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues_enum': 'missing_sections',
                'critical_issues': {
                    'sections': [{'name': 'Header', 'status': 'missing', 'description': 'Header missing'}],
                    'summary': 'Missing critical sections'
                },
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Missing sections detected'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["status"] == "fail"

def test_parse_multi_page_analysis_results_significant_visual_changes():
    """Test status determination when significant visual changes are present."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues_enum': 'none',
                'visual_changes_enum': 'significant',
                'recommendation_enum': 'review_required',
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Significant changes detected'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["status"] == "warning"

def test_parse_multi_page_analysis_results_minor_visual_changes():
    """Test status determination when minor visual changes are present."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues_enum': 'none',
                'visual_changes_enum': 'minor',
                'recommendation_enum': 'pass',
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Minor changes detected'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["status"] == "warning"

def test_parse_multi_page_analysis_results_string_based_fallback():
    """Test fallback to string-based analysis when visual_analysis is not a dict."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': "Found missing sections in the layout",
            'sections_analysis': 'String-based analysis'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["status"] == "fail"

def test_parse_multi_page_analysis_results_string_based_significant_changes():
    """Test string-based analysis with significant changes."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': "Found significant changes in the layout",
            'sections_analysis': 'String-based analysis'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["status"] == "warning"

def test_parse_multi_page_analysis_results_string_based_pass():
    """Test string-based analysis with no issues."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': "No significant changes detected",
            'sections_analysis': 'String-based analysis'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["status"] == "pass"

def test_parse_multi_page_analysis_results_multiple_pages():
    """Test processing multiple pages with different statuses."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues_enum': 'none',
                'visual_changes_enum': 'minor',
                'recommendation_enum': 'pass',
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Page 1 analysis'
        },
        {
            'page_path': '/about',
            'base_url': 'https://example.com/about',
            'pr_url': 'https://preview.example.com/about',
            'visual_analysis': {
                'critical_issues_enum': 'missing_sections',
                'visual_changes_enum': 'none',
                'recommendation_enum': 'review_required',
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Page 2 analysis'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    assert len(result["reports"]) == 2
    assert result["reports"][0]["status"] == "warning"  # minor changes
    assert result["reports"][1]["status"] == "fail"     # critical issues

def test_parse_multi_page_analysis_results_with_image_refs():
    """Test processing with image references."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Analysis with images',
            'image_refs': {
                'base_screenshot': 'base64_encoded_image_1',
                'pr_screenshot': 'base64_encoded_image_2',
                'diff_image': 'base64_encoded_image_3'
            }
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["image_refs"] is not None
    assert report["image_refs"]["base_screenshot"] == 'base64_encoded_image_1'
    assert report["image_refs"]["pr_screenshot"] == 'base64_encoded_image_2'
    assert report["image_refs"]["diff_image"] == 'base64_encoded_image_3'

def test_parse_multi_page_analysis_results_without_image_refs():
    """Test processing without image references."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Analysis without images'
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["image_refs"] is None

def test_parse_multi_page_analysis_results_empty_page_results():
    """Test handling of empty page results list."""
    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=[]
    )

    assert isinstance(result, dict)
    assert result["test_data"]["pr_number"] == "123"
    assert result["test_data"]["repository"] == "test/repo"
    assert len(result["reports"]) == 0

def test_parse_multi_page_analysis_results_missing_optional_fields():
    """Test handling of missing optional fields in page results."""
    page_results = [
        {
            'page_path': '/',
            'base_url': 'https://example.com',
            'pr_url': 'https://preview.example.com',
            'visual_analysis': {
                'critical_issues': {'sections': [], 'summary': ''},
                'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
            },
            'sections_analysis': 'Analysis'
            # image_refs intentionally omitted
        }
    ]

    result = parse_multi_page_analysis_results(
        pr_number="123",
        repository="test/repo",
        page_results=page_results
    )

    report = result["reports"][0]
    assert report["image_refs"] is None
    assert report["status"] == "pass"

def test_parse_multi_page_analysis_results_complex_status_logic():
    """Test complex status determination logic with various combinations."""
    test_cases = [
        # (critical_issues_enum, visual_changes_enum, recommendation_enum, expected_status)
        ('none', 'none', 'pass', 'pass'),
        ('missing_sections', 'none', 'pass', 'fail'),
        ('other_issues', 'none', 'pass', 'fail'),
        ('none', 'significant', 'pass', 'warning'),
        ('none', 'minor', 'pass', 'warning'),
        ('none', 'none', 'review_required', 'warning'),
        ('none', 'significant', 'review_required', 'warning'),
    ]

    for critical_issues_enum, visual_changes_enum, recommendation_enum, expected_status in test_cases:
        page_results = [
            {
                'page_path': '/',
                'base_url': 'https://example.com',
                'pr_url': 'https://preview.example.com',
                'visual_analysis': {
                    'critical_issues_enum': critical_issues_enum,
                    'visual_changes_enum': visual_changes_enum,
                    'recommendation_enum': recommendation_enum,
                    'critical_issues': {'sections': [], 'summary': ''},
                    'structural_analysis': {'section_order': '', 'layout': '', 'broken_layouts': ''},
                    'visual_changes': {'diff_highlights': [], 'animation_issues': '', 'conclusion': ''},
                    'conclusion': {'critical_issues': '', 'visual_changes': '', 'recommendation': '', 'summary': ''}
                },
                'sections_analysis': f'Test case: {critical_issues_enum}, {visual_changes_enum}, {recommendation_enum}'
            }
        ]

        result = parse_multi_page_analysis_results(
            pr_number="123",
            repository="test/repo",
            page_results=page_results
        )

        report = result["reports"][0]
        assert report["status"] == expected_status, f"Expected {expected_status} for {critical_issues_enum}, {visual_changes_enum}, {recommendation_enum}"
