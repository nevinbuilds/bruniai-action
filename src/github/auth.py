import os
import logging

logger = logging.getLogger("agent-runner")

def get_github_app_token():
    """Get the GitHub Actions token from the environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("Missing GITHUB_TOKEN environment variable")
        return None
    return token
