from datetime import datetime
import uuid
from typing import Dict, Any
from .types import (
    ReportData,
    ReportStatus,
    CriticalIssuesStatus,
    VisualChangesStatus,
    RecommendationStatus,
)

def parse_analysis_results(
    base_url: str,
    preview_url: str,
    pr_number: str,
    repository: str,
    visual_analysis: Dict[str, Any],  # Now expects structured data instead of string
) -> ReportData:
    """
    Parse the analysis results and generate a structured report.
    """
    # Generate default report structure
    report: ReportData = {
        "id": str(uuid.uuid4()),
        "url": base_url,
        "preview_url": preview_url,
        "repository": repository,
        "pr_number": pr_number,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
        "status_enum": "none",
        "critical_issues": {
            "sections": [],
            "summary": "",
        },
        "critical_issues_enum": "none",
        "structural_analysis": {
            "section_order": "",
            "layout": "",
            "broken_layouts": "",
        },
        "visual_changes": {
            "diff_highlights": [],
            "animation_issues": "",
            "conclusion": "",
        },
        "visual_changes_enum": "none",
        "conclusion": {
            "critical_issues": "",
            "visual_changes": "",
            "recommendation": "",
            "summary": "",
        },
        "recommendation_enum": "pass",
        "created_at": datetime.utcnow().isoformat(),
    }

    # Handle case where visual_analysis might still be a string (for backward compatibility)
    if isinstance(visual_analysis, str):
        # Fallback to old parsing logic
        if "missing sections" in visual_analysis.lower():
            report["critical_issues_enum"] = "missing_sections"
        if "significant changes" in visual_analysis.lower():
            report["visual_changes_enum"] = "significant"
            report["recommendation_enum"] = "review_required"
        elif "minor changes" in visual_analysis.lower():
            report["visual_changes_enum"] = "minor"
    else:
        # Parse structured visual analysis data
        try:
            # Extract status enum directly from response
            report["status_enum"] = visual_analysis.get("status_enum", "none")
            report["status"] = visual_analysis.get("status_enum", "none")  # Keep backward compatibility

            # Extract critical issues
            critical_issues = visual_analysis.get("critical_issues", {})
            report["critical_issues"]["sections"] = critical_issues.get("sections", [])
            report["critical_issues"]["summary"] = critical_issues.get("summary", "")

            # Extract critical issues enum directly from response
            report["critical_issues_enum"] = visual_analysis.get("critical_issues_enum", "none")

            # Extract structural analysis
            structural = visual_analysis.get("structural_analysis", {})
            report["structural_analysis"]["section_order"] = structural.get("section_order", "")
            report["structural_analysis"]["layout"] = structural.get("layout", "")
            report["structural_analysis"]["broken_layouts"] = structural.get("broken_layouts", "")

            # Extract visual changes
            visual_changes = visual_analysis.get("visual_changes", {})
            report["visual_changes"]["diff_highlights"] = visual_changes.get("diff_highlights", [])
            report["visual_changes"]["animation_issues"] = visual_changes.get("animation_issues", "")
            report["visual_changes"]["conclusion"] = visual_changes.get("conclusion", "")

            # Extract visual changes enum directly from response
            report["visual_changes_enum"] = visual_analysis.get("visual_changes_enum", "none")

            # Extract conclusion
            conclusion = visual_analysis.get("conclusion", {})
            report["conclusion"]["critical_issues"] = conclusion.get("critical_issues", "")
            report["conclusion"]["visual_changes"] = conclusion.get("visual_changes", "")
            report["conclusion"]["recommendation"] = conclusion.get("recommendation", "pass")
            report["conclusion"]["summary"] = conclusion.get("summary", "")

            # Extract recommendation enum directly from response
            report["recommendation_enum"] = visual_analysis.get("recommendation_enum", "pass")

        except Exception as e:
            # Fallback in case of parsing errors
            report["conclusion"]["summary"] = f"Error parsing visual analysis: {str(e)}"
            report["recommendation_enum"] = "review_required"
            report["status_enum"] = "fail"
            report["status"] = "fail"
            report["critical_issues_enum"] = "other_issues"

    # Set overall status based on findings (only for string-based fallback)
    if isinstance(visual_analysis, str):
        if report["critical_issues_enum"] != "none":
            report["status"] = "fail"
            report["status_enum"] = "fail"
        elif report["visual_changes_enum"] == "significant" or report["recommendation_enum"] == "review_required":
            report["status"] = "warning"
            report["status_enum"] = "warning"
        else:
            report["status"] = "pass"
            report["status_enum"] = "pass"

    return report
