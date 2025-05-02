import os
import json
import logging
import requests

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
    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")  # e.g. 'org/repo'
    pr_number = os.getenv("PR_NUMBER") or get_pr_number_from_event()

    logger.info(f"GITHUB_TOKEN: {github_token}")
    logger.info(f"GITHUB_REPOSITORY: {repo}")
    logger.info(f"PR_NUMBER: {pr_number}")

    if not all([github_token, repo, pr_number]):
        logger.warning("Missing GitHub context, skipping PR comment.")
        return

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
        if comment["body"].startswith("# URL Comparison Analysis"):
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
