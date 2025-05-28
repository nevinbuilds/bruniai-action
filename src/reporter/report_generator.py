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
    sections_analysis: str,
    visual_analysis: str,
) -> ReportData:
    """
    Parse the analysis results and generate a structured report.
    """
    # Generate default report structure
    report: ReportData = {
        "id": str(uuid.uuid4()),
        "url": base_url,
        "preview_url": preview_url,
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

    # Parse sections analysis
    # TODO: Implement proper parsing of sections_analysis string
    if "missing sections" in sections_analysis.lower():
        report["critical_issues_enum"] = "missing_sections"

    # Parse visual analysis
    # TODO: Implement proper parsing of visual_analysis string
    if "significant changes" in visual_analysis.lower():
        report["visual_changes_enum"] = "significant"
        report["recommendation_enum"] = "review_required"
    elif "minor changes" in visual_analysis.lower():
        report["visual_changes_enum"] = "minor"

    # Set overall status based on findings
    if report["critical_issues_enum"] != "none":
        report["status"] = "fail"
        report["status_enum"] = "fail"
    elif report["visual_changes_enum"] == "significant":
        report["status"] = "warning"
        report["status_enum"] = "warning"
    else:
        report["status"] = "pass"
        report["status_enum"] = "pass"

    return report
