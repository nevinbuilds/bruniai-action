from datetime import datetime
import uuid
from typing import Dict, Any, Optional, List
from .types import (
    MultiPageReportData,
    TestData,
    PageReport,
)

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
            elif ("significant changes" in analysis_text and "no significant changes" not in analysis_text) or "review required" in analysis_text:
                status = "warning"
            else:
                status = "pass"

        # Parse the visual analysis to extract structured data
        # (Assume visual_analysis is already structured for multi-page)
        if isinstance(visual_analysis, dict):
            parsed_report = visual_analysis
        else:
            # Create default structured data for string-based analysis
            parsed_report = {
                "critical_issues": {"sections": [], "summary": ""},
                "structural_analysis": {"section_order": "", "layout": "", "broken_layouts": ""},
                "visual_changes": {"diff_highlights": [], "animation_issues": "", "conclusion": ""},
                "conclusion": {"critical_issues": "", "visual_changes": "", "recommendation": "", "summary": ""}
            }

        # Create page report with guaranteed valid status
        page_report: PageReport = {
            "page_path": page_path,
            "url": base_url,
            "preview_url": pr_url,
            "status": status,  # Use our determined status instead of parsed one
            "critical_issues": parsed_report["critical_issues"],
            "critical_issues_enum": visual_analysis.get("critical_issues_enum", "none") if isinstance(visual_analysis, dict) else ("missing_sections" if "missing sections" in str(visual_analysis).lower() else "other_issues" if "critical" in str(visual_analysis).lower() else "none"),
            "structural_analysis": parsed_report["structural_analysis"],
            "visual_changes": parsed_report["visual_changes"],
            "visual_changes_enum": visual_analysis.get("visual_changes_enum", "none") if isinstance(visual_analysis, dict) else ("significant" if "significant changes" in str(visual_analysis).lower() and "no significant changes" not in str(visual_analysis).lower() else "minor" if "minor" in str(visual_analysis).lower() else "none"),
            "recommendation_enum": visual_analysis.get("recommendation_enum", "pass") if isinstance(visual_analysis, dict) else ("review_required" if "review required" in str(visual_analysis).lower() else "pass"),
            "conclusion": parsed_report["conclusion"],
            "image_refs": image_refs
        }

        reports.append(page_report)

    return {
        "test_data": test_data,
        "reports": reports
    }
