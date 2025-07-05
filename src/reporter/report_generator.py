from datetime import datetime
import uuid
from typing import Dict, Any, Optional, List
from .types import (
    ReportStatus,
    CriticalIssuesStatus,
    VisualChangesStatus,
    RecommendationStatus,
    MultiPageReportData,
    TestData,
    PageReport,
    CriticalIssues,
    StructuralAnalysis,
    VisualChanges,
    Conclusion,
)

def _parse_analysis_results_internal(
    base_url: str,
    preview_url: str,
    pr_number: str,
    repository: str,
    visual_analysis: Dict[str, Any],
    image_refs: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Internal function to parse analysis results for use in multi-page reports.
    """
    # Generate default report structure
    report = {
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
            report["critical_issues_enum"] = "other_issues"

    return report

def parse_multi_page_analysis_results(
    pr_number: str,
    repository: str,
    page_results: List[Dict[str, Any]]
) -> MultiPageReportData:
    """
    Parse multiple page analysis results and generate a structured multi-page report.

    Args:
        pr_number: PR number
        repository: Repository name
        page_results: List of page result dictionaries containing:
            - page_path: str
            - base_url: str
            - pr_url: str
            - visual_analysis: Dict[str, Any]
            - sections_analysis: str
            - image_refs: Optional[Dict[str, str]]

    Returns:
        MultiPageReportData with test_data and reports
    """
    # Create test data
    test_data: TestData = {
        "pr_number": pr_number,
        "repository": repository,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Process each page result
    reports: List[PageReport] = []

    for page_result in page_results:
        page_path = page_result['page_path']
        base_url = page_result['base_url']
        pr_url = page_result['pr_url']
        visual_analysis = page_result['visual_analysis']
        sections_analysis = page_result['sections_analysis']
        image_refs = page_result.get('image_refs')

        # Determine status based on visual analysis
        status = "pass"  # Default to pass
        if isinstance(visual_analysis, dict):
            # Check for critical issues
            critical_issues_enum = visual_analysis.get("critical_issues_enum", "none")
            if critical_issues_enum != "none":
                status = "fail"
            else:
                # Check for visual changes
                visual_changes_enum = visual_analysis.get("visual_changes_enum", "none")
                recommendation_enum = visual_analysis.get("recommendation_enum", "pass")

                if visual_changes_enum == "significant" or recommendation_enum == "review_required":
                    status = "warning"
                elif visual_changes_enum == "minor":
                    status = "warning"
                else:
                    status = "pass"
        else:
            # Fallback for string-based analysis
            analysis_text = str(visual_analysis).lower()
            if "missing sections" in analysis_text or "critical" in analysis_text:
                status = "fail"
            elif "significant changes" in analysis_text or "review required" in analysis_text:
                status = "warning"
            else:
                status = "pass"

        # Parse the visual analysis to extract structured data
        parsed_report = _parse_analysis_results_internal(
            base_url, pr_url, pr_number, repository, visual_analysis, image_refs
        )

        # Create page report with guaranteed valid status
        page_report: PageReport = {
            "page_path": page_path,
            "url": base_url,
            "preview_url": pr_url,
            "status": status,  # Use our determined status instead of parsed one
            "critical_issues": parsed_report["critical_issues"],
            "structural_analysis": parsed_report["structural_analysis"],
            "visual_changes": parsed_report["visual_changes"],
            "conclusion": parsed_report["conclusion"],
            "image_refs": image_refs
        }

        reports.append(page_report)

    return {
        "test_data": test_data,
        "reports": reports
    }
