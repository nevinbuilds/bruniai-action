from typing import List, TypedDict, Literal, Optional
from datetime import datetime

ReportStatus = Literal['pass', 'fail', 'warning', 'none']
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

class ReportData(TypedDict):
    id: Optional[str]  # UUID
    url: str
    preview_url: str
    repository: str
    pr_number: str
    timestamp: str
    status: str  # Keep for backward compatibility
    status_enum: Optional[ReportStatus]
    critical_issues: CriticalIssues
    critical_issues_enum: Optional[CriticalIssuesStatus]
    structural_analysis: StructuralAnalysis
    visual_changes: VisualChanges
    visual_changes_enum: Optional[VisualChangesStatus]
    conclusion: Conclusion
    recommendation_enum: Optional[RecommendationStatus]
    created_at: Optional[str]  # timestamp
    user_id: Optional[str]  # UUID
