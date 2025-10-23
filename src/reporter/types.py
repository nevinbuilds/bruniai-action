from typing import List, TypedDict, Literal, Optional, Dict
from datetime import datetime

ReportStatus = Literal['pass', 'fail', 'warning']
CriticalIssuesStatus = Literal['none', 'missing_sections', 'other_issues']
VisualChangesStatus = Literal['none', 'minor', 'significant']
RecommendationStatus = Literal['pass', 'review_required', 'reject']

class SectionInfo(TypedDict):
    name: str
    status: str
    description: str

class CriticalIssues(TypedDict):
    sections: List[SectionInfo]
    summary: str

class StructuralAnalysis(TypedDict):
    section_order: str
    layout: str
    broken_layouts: str

class VisualChanges(TypedDict):
    diff_highlights: List[str]
    animation_issues: str
    conclusion: str

class Conclusion(TypedDict):
    critical_issues: str
    visual_changes: str
    recommendation: str
    summary: str

class ImageReferences(TypedDict):
    base_screenshot: Optional[str]  # Base64 encoded image data
    pr_screenshot: Optional[str]    # Base64 encoded image data
    diff_image: Optional[str]       # Base64 encoded image data
    section_screenshots: Optional[Dict[str, Dict[str, str]]]  # Section screenshots with structure: {section_id: {base: "base64", pr: "base64"}}

# Multi-page API types
class TestData(TypedDict):
    pr_number: str
    repository: str
    timestamp: str

class PageReport(TypedDict):
    page_path: str
    url: str
    preview_url: str
    status: ReportStatus  # Required and cannot be 'none'
    critical_issues: CriticalIssues
    critical_issues_enum: CriticalIssuesStatus
    structural_analysis: StructuralAnalysis
    visual_changes: VisualChanges
    visual_changes_enum: VisualChangesStatus
    recommendation_enum: RecommendationStatus
    conclusion: Conclusion
    image_refs: Optional[ImageReferences]

class MultiPageReportData(TypedDict):
    test_data: TestData
    reports: List[PageReport]
