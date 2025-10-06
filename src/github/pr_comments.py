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

def post_pr_comment(visual_analysis: dict, report_url: str = None):
    # Get GitHub App token.
    github_token = get_github_app_token()
    if not github_token:
        logger.error("Failed to get GitHub App token.")
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

    # Generate artifact URL.
    artifacts_url = None
    if run_id:
        artifacts_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    # Format the visual analysis into markdown.
    summary = format_visual_analysis_to_markdown(
        visual_analysis, report_url, artifacts_url)

    # First, try to find an existing comment from our tool.
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get all comments for the PR.
    comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    response = requests.get(comments_url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch comments: {response.text}")
        return

    comments = response.json()
    existing_comment_id = None

    # Look for a comment that starts with our header.
    for comment in comments:
        if comment["body"].startswith("Information about visual testing analysis provided by [bruniai]"):
            existing_comment_id = comment["id"]
            break

    if existing_comment_id:
        # Update existing comment.
        update_url = f"https://api.github.com/repos/{repo}/issues/comments/{existing_comment_id}"
        response = requests.patch(update_url, json={"body": summary}, headers=headers)

        if response.status_code == 200:
            logger.info("📝 Successfully updated existing PR comment.")
        else:
            logger.error("❌ Failed to update PR comment: %s", response.text)
    else:
        # Create new comment.
        response = requests.post(comments_url, json={"body": summary}, headers=headers)

        if response.status_code == 201:
            logger.info("📝 Successfully created new PR comment.")
        else:
            logger.error("❌ Failed to create PR comment: %s", response.text)

def format_visual_analysis_to_markdown(visual_analysis: dict, report_url: str = None, artifacts_url: str = None) -> str:
    """Convert structured visual analysis JSON to readable markdown format."""
    if not visual_analysis or not isinstance(visual_analysis, dict):
        return "❌ **Error**: No visual analysis data available."

    markdown_parts = []

    # Overall Report Header.
    overall_recommendation = visual_analysis.get("overall_recommendation_enum", "unknown")
    overall_status_emoji = {
        "pass": "✅",
        "review_required": "⚠️",
        "reject": "❌"
    }.get(overall_recommendation, "❓")

    num_pages = len(visual_analysis.get("pages", []))
    markdown_parts.append(f"# {overall_status_emoji} Visual Testing Report — {overall_recommendation.replace('_', ' ').title()}\n")
    markdown_parts.append(f"*{num_pages} pages analyzed by [bruniai](https://www.brunivisual.com/)*  \n")

    if artifacts_url:
        markdown_parts.append(f"[📦 View Artifacts]({artifacts_url})\n")

    # Iterate through pages.
    for i, page_analysis in enumerate(visual_analysis.get("pages", [])):
        markdown_parts.append("\n---\n") # Separator for pages.

        page_name = page_analysis.get("page_name", f"Page {i+1}")
        markdown_parts.append(f"## Page {i+1}: `{page_name}`\n")

        # Critical Sections Check.
        critical_issues = page_analysis.get("critical_issues", {})
        sections = critical_issues.get("sections", [])
        if sections:
            markdown_parts.append("### 🚨 Critical Sections Check\n")
            markdown_parts.append("| Section | Status |\n")
            markdown_parts.append("|----------------------------------------|--------|\n")
            for section in sections:
                name = section.get("name", "Unknown Section")
                status = section.get("status", "Unknown")
                status_icon = "❌" if status == "Missing" else "✅"
                markdown_parts.append(f"| {name:<38} | {status_icon} |\n")
            markdown_parts.append("\n")

        # Visual Changes.
        visual_changes = page_analysis.get("visual_changes", {})
        if visual_changes and any(visual_changes.values()):
            markdown_parts.append("### 🎨 Visual Changes\n")

            diff_highlights = visual_changes.get("diff_highlights", [])
            for highlight in diff_highlights:
                markdown_parts.append(f"- {highlight}\n")

            animation_issues = visual_changes.get("animation_issues", "")
            if animation_issues:
                markdown_parts.append(f"- {animation_issues}\n")

            conclusion = visual_changes.get("conclusion", "")
            if conclusion:
                markdown_parts.append(f"- {conclusion}\n")
            markdown_parts.append("\n")

        # Structural Analysis.
        structural = page_analysis.get("structural_analysis", {})
        if structural and any(structural.values()):
            markdown_parts.append("### 🏗️ Structure\n")

            section_order = structural.get("section_order", "")
            if section_order:
                markdown_parts.append(f"- Section order {section_order}\n")

            layout = structural.get("layout", "")
            if layout:
                markdown_parts.append(f"- Layout {layout}\n")

            broken_layouts = structural.get("broken_layouts", "")
            if broken_layouts:
                markdown_parts.append(f"- {broken_layouts}\n")
            markdown_parts.append("\n")

            # Reference Structure (collapsible section).
            structural_analysis_details = structural.get("structural_analysis_details", "")
            if structural_analysis_details:
                markdown_parts.append("<details>\n<summary>📖 Reference Structure (click to expand)</summary>\n\n")
                markdown_parts.append(f"*{structural_analysis_details}*\n\n")
                markdown_parts.append("</details>\n")

    return "".join(markdown_parts)
