import os
import json
import logging
import requests
from .auth import get_github_app_token

logger = logging.getLogger("agent-runner")

def get_pr_number_from_event():
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path or not os.getenv("GITHUB_REPOSITORY"):
        logger.warning("GITHUB_EVENT_PATH not found or GITHUB_REPOSITORY not set.")
        return None

    try:
        with open(event_path, 'r') as f:
            event = json.load(f)

        pr_number = (
            event.get("pull_request", {}).get("number") or
            event.get("issue", {}).get("number")
        )

        if not pr_number:
            logger.warning("PR number not found in event payload.")
        return pr_number
    except Exception as e:
        logger.error("Error reading PR number from event: %s", e)
        return None

def post_pr_comment(summary: str):
    # Get GitHub App token
    github_token = get_github_app_token()
    if not github_token:
        logger.error("Failed to get GitHub App token")
        return

    repo = os.getenv("GITHUB_REPOSITORY")  # e.g. 'org/repo'
    pr_number = os.getenv("PR_NUMBER") or get_pr_number_from_event()
    run_id = os.getenv("GITHUB_RUN_ID")

    logger.info(f"GITHUB_REPOSITORY: {repo}")
    logger.info(f"PR_NUMBER: {pr_number}")
    logger.info(f"GITHUB_RUN_ID: {run_id}")

    if not all([github_token, repo, pr_number]):
        logger.warning("Missing GitHub context, skipping PR comment.")
        return

    # Add artifact links to the summary
    if run_id:
        artifacts_url = f"https://github.com/{repo}/actions/runs/{run_id}"
        summary = f"{summary}\n\n📦 [View Artifacts]({artifacts_url}) for more details including screenshots."

    # First, try to find an existing comment from our tool
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get all comments for the PR
    comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    response = requests.get(comments_url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch comments: {response.text}")
        return

    comments = response.json()
    existing_comment_id = None

    # Look for a comment that starts with our header
    for comment in comments:
        if comment["body"].startswith("Information about visual testing analysis provided by [bruniai]"):
            existing_comment_id = comment["id"]
            break

    if existing_comment_id:
        # Update existing comment
        update_url = f"https://api.github.com/repos/{repo}/issues/comments/{existing_comment_id}"
        response = requests.patch(update_url, json={"body": summary}, headers=headers)

        if response.status_code == 200:
            logger.info("📝 Successfully updated existing PR comment.")
        else:
            logger.error("❌ Failed to update PR comment: %s", response.text)
    else:
        # Create new comment
        response = requests.post(comments_url, json={"body": summary}, headers=headers)

        if response.status_code == 201:
            logger.info("📝 Successfully created new PR comment.")
        else:
            logger.error("❌ Failed to create PR comment: %s", response.text)

def format_visual_analysis_to_markdown(visual_analysis: dict) -> str:
    """Convert structured visual analysis JSON to readable markdown format."""
    if not visual_analysis or not isinstance(visual_analysis, dict):
        return "❌ **Error**: No visual analysis data available"
    
    markdown_parts = []
    
    recommendation = visual_analysis.get("recommendation_enum", "unknown")
    status_emoji = {
        "pass": "✅",
        "review_required": "⚠️", 
        "reject": "❌"
    }.get(recommendation, "❓")
    
    markdown_parts.append(f"## {status_emoji} **Recommendation: {recommendation.replace('_', ' ').title()}**\n")
    
    critical_issues = visual_analysis.get("critical_issues", {})
    if critical_issues and (critical_issues.get("sections") or critical_issues.get("summary")):
        markdown_parts.append("### 🚨 Critical Issues")
        
        sections = critical_issues.get("sections", [])
        if sections:
            markdown_parts.append("**Section Status:**")
            for section in sections:
                name = section.get("name", "Unknown Section")
                status = section.get("status", "Unknown")
                description = section.get("description", "")
                status_icon = "❌" if status == "Missing" else "✅"
                markdown_parts.append(f"- {status_icon} **{name}**: {status}")
                if description and status == "Missing":
                    markdown_parts.append(f"  - {description}")
        
        summary = critical_issues.get("summary", "")
        if summary:
            markdown_parts.append(f"**Summary:** {summary}")
        markdown_parts.append("")
    
    visual_changes = visual_analysis.get("visual_changes", {})
    if visual_changes and any(visual_changes.values()):
        markdown_parts.append("### 🎨 Visual Changes")
        
        diff_highlights = visual_changes.get("diff_highlights", [])
        if diff_highlights:
            markdown_parts.append("**Key Differences:**")
            for highlight in diff_highlights:
                markdown_parts.append(f"- {highlight}")
        
        animation_issues = visual_changes.get("animation_issues", "")
        if animation_issues:
            markdown_parts.append(f"**Animation Notes:** {animation_issues}")
            
        conclusion = visual_changes.get("conclusion", "")
        if conclusion:
            markdown_parts.append(f"**Analysis:** {conclusion}")
        markdown_parts.append("")
    
    structural = visual_analysis.get("structural_analysis", {})
    if structural and any(structural.values()):
        markdown_parts.append("### 🏗️ Structural Analysis")
        
        section_order = structural.get("section_order", "")
        if section_order:
            markdown_parts.append(f"**Section Order:** {section_order}")
            
        layout = structural.get("layout", "")
        if layout:
            markdown_parts.append(f"**Layout:** {layout}")
            
        broken_layouts = structural.get("broken_layouts", "")
        if broken_layouts:
            markdown_parts.append(f"**Issues:** {broken_layouts}")
        markdown_parts.append("")
    
    conclusion = visual_analysis.get("conclusion", {})
    if conclusion and conclusion.get("summary"):
        markdown_parts.append("### 📋 Summary")
        summary = conclusion.get("summary", "")
        if summary:
            markdown_parts.append(summary)
        markdown_parts.append("")
    
    return "\n".join(markdown_parts)
