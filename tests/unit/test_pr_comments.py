"""
Test suite for GitHub PR comment functionality.

This module tests the PR comment management functions which are responsible for:
1. Posting and updating comments on GitHub Pull Requests
2. Extracting PR numbers from GitHub event data
3. Managing GitHub API interactions
4. Handling authentication and environment variables

The tests cover various scenarios:
- Updating existing comments
- Creating new comments
- Extracting PR information from GitHub events
"""

import pytest
from unittest.mock import patch, mock_open
from src.github.pr_comments import (
    post_pr_comment,
    get_pr_number_from_event,
    format_visual_analysis_to_markdown,
    format_multi_page_analysis_to_markdown,
)

def test_post_pr_comment_update_existing():
    """
    Test updating an existing PR comment.

    Verifies that when a comment already exists:
    1. The function finds the existing comment
    2. Updates it with new content instead of creating a duplicate
    3. Uses the correct GitHub API endpoint and authentication
    4. Handles environment variables properly
    """
    # Mock requests.get to return a fake response with an existing comment
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"id": 1, "body": "Information about visual testing analysis provided by [bruniai]"}]
        # Mock requests.patch to simulate updating the comment
        with patch("requests.patch") as mock_patch:
            mock_patch.return_value.status_code = 200
            # Mock get_github_app_token to return a fake token
            with patch("src.github.pr_comments.get_github_app_token", return_value="fake_token"):
                # Mock os.getenv to return fake repo, PR number, and run ID
                with patch("os.getenv", side_effect=lambda key: {"GITHUB_REPOSITORY": "org/repo", "PR_NUMBER": "123", "GITHUB_RUN_ID": "456"}.get(key)):
                    # Create test structured data
                    test_visual_analysis = {
                        "overall_recommendation_enum": "pass",
                        "pages": [{
                            "page_name": "/",
                            "critical_issues": {"sections": []},
                            "visual_changes": {},
                            "structural_analysis": {}
                        }]
                    }
                    post_pr_comment(test_visual_analysis)
                    mock_patch.assert_called_once()

def test_get_pr_number_from_event_success():
    """
    Test extracting PR number from GitHub event data.

    Verifies that the function:
    1. Correctly reads the GitHub event file
    2. Parses the JSON payload
    3. Extracts the PR number from the event data
    4. Handles environment variables properly
    """
    # Mock os.getenv to return a fake event path
    with patch("os.getenv", side_effect=lambda key: {"GITHUB_EVENT_PATH": "/fake/path", "GITHUB_REPOSITORY": "org/repo"}.get(key)):
        # Mock open to return a fake event JSON payload
        with patch("builtins.open", mock_open(read_data='{"pull_request": {"number": 123}}')):
            pr_number = get_pr_number_from_event()
            assert pr_number == 123


def test_format_visual_analysis_to_markdown_single_page():
    """
    Ensure single-page formatter outputs the new markdown sections and content.
    """
    visual_analysis = {
        "critical_issues_enum": "none",
        "visual_changes_enum": "minor",
        "recommendation_enum": "pass",
        "critical_issues": {
            "sections": [
                {"name": "Hero", "status": "Present"},
                {"name": "Footer", "status": "Missing"},
            ],
            "summary": "Footer is missing.",
        },
        "visual_changes": {
            "diff_highlights": ["Button color changed"],
            "animation_issues": "Carousel animates.",
            "conclusion": "Minor visual adjustments.",
        },
        "structural_analysis": {
            "section_order": "remains the same.",
            "layout": "No major layout changes.",
            "broken_layouts": "",
        },
    }

    md = format_visual_analysis_to_markdown(
        visual_analysis, report_url="https://example.com/artifacts"
    )

    # Header reflects warning due to minor visual changes.
    assert "## ⚠️ Visual Testing Report — Warning" in md
    # Branding line.
    assert "*1 page analyzed by [bruniai](https://www.brunivisual.com/)*" in md
    # Artifacts link.
    assert "[📦 View Artifacts](https://example.com/artifacts)" in md
    # Critical sections table and entries.
    assert "### 🚨 Critical Sections Check" in md
    assert "Hero" in md
    assert "Footer" in md
    assert "❌" in md  # Missing footer row uses cross icon.
    assert "✅" in md  # Present hero row uses check icon.
    # Visual changes section and items.
    assert "### 🎨 Visual Changes" in md
    assert "- Button color changed" in md
    assert "- Carousel animates." in md
    assert "- Minor visual adjustments." in md
    # Structure section and details.
    assert "### 🏗️ Structure" in md
    assert "- Section order remains the same." in md
    assert "- Layout No major layout changes." in md
    # Collapsible reference block.
    assert "<details>" in md and "</details>" in md
    assert "Reference Structure (click to expand)" in md


def test_format_multi_page_analysis_to_markdown_multiple_pages():
    """
    Ensure multi-page formatter produces overall status, summary table and details.
    """
    reports = [
        {
            "page_path": "/home",
            "critical_issues_enum": "missing_sections",  # Should drive fail
            "visual_changes_enum": "none",
            "recommendation_enum": "reject",
            "critical_issues": {"sections": [{"name": "Hero", "status": "Missing"}]},
        },
        {
            "page_path": "/contact",
            "critical_issues_enum": "none",
            "visual_changes_enum": "minor",  # Should drive warning
            "recommendation_enum": "pass",
            "visual_changes": {"conclusion": "Minor changes."},
        },
    ]

    md = format_multi_page_analysis_to_markdown(
        reports, report_url="https://example.com/artifacts"
    )

    # Overall header should be Fail due to first report failing.
    assert "## ❌ Visual Testing Report — Fail" in md
    # Summary section with both pages and status icons.
    assert "## 📊 Summary" in md
    assert "| /home | ❌ fail |" in md
    assert "| /contact | ⚠️ warning |" in md
    # Artifacts link at top-level when provided.
    assert "[📦 View Artifacts](https://example.com/artifacts)" in md
    # Details blocks for each page present with correct summaries.
    assert "<summary>❌ Page 1: /home (fail)</summary>" in md
    assert "<summary>⚠️ Page 2: /contact (warning)</summary>" in md
    assert md.count("<details>") >= 2 and md.count("</details>") >= 2
