import requests
import os
import logging
from .auth import get_github_app_token
from .pr_comments import get_pr_number_from_event

logger = logging.getLogger("agent-runner")

def fetch_pr_metadata():
    # Get GitHub App token
    github_token = get_github_app_token()
    if not github_token:
        logger.error("Failed to get GitHub App token")
        return None, None

    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER") or get_pr_number_from_event()

    if not github_token or not repo or not pr_number:
        logger.warning("Cannot fetch PR metadata: missing token, repo, or PR number")
        return None, None

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("title"), data.get("body")
    else:
        logger.error(f"Failed to fetch PR metadata: {response.status_code} {response.text}")
        return None, None
