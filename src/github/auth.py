import os
import json
import jwt
import time
import requests
import logging

logger = logging.getLogger("agent-runner")

# Hardcoded App ID
APP_ID = "1239933"

def get_installation_id():
    """Get the installation ID from the event payload or REST API."""
    # First try to get from webhook event
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path:
        try:
            with open(event_path, 'r') as f:
                event = json.load(f)
                # Log the event payload for debugging
                logger.info("Event payload:")
                logger.info(json.dumps(event, indent=2))

                # Try different possible locations for the installation ID
                installation_id = (
                    event.get("installation", {}).get("id") or
                    event.get("repository", {}).get("installation_id")
                )
                if installation_id:
                    logger.info(f"Found installation ID in event payload: {installation_id}")
                    return str(installation_id)
        except Exception as e:
            logger.error(f"Error reading installation ID from event: {e}")

    # If not found in event, try to get from REST API
    try:
        # First get a JWT for the app
        private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
        if not private_key:
            logger.error("Missing GITHUB_APP_PRIVATE_KEY")
            return None

        # Generate JWT
        payload = {
            'iat': int(time.time()),
            'exp': int(time.time()) + 600,  # 10 minutes
            'iss': APP_ID
        }
        encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256')

        # Get repository info from environment
        repo = os.getenv("GITHUB_REPOSITORY")  # format: owner/repo
        if not repo:
            logger.error("Missing GITHUB_REPOSITORY")
            return None

        owner, repo_name = repo.split('/')

        # Get installation ID from REST API
        headers = {
            'Authorization': f'Bearer {encoded_jwt}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/installation',
            headers=headers
        )

        if response.status_code == 200:
            installation_id = response.json().get('id')
            if installation_id:
                logger.info(f"Found installation ID from REST API: {installation_id}")
                return str(installation_id)
        else:
            logger.error(f"Failed to get installation ID from REST API: {response.text}")

    except Exception as e:
        logger.error(f"Error getting installation ID from REST API: {e}")

    logger.error("Could not determine installation ID")
    return None

def get_github_app_token():
    """Get a GitHub App installation access token."""
    # Get the private key from the environment
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    if not private_key:
        logger.error("Missing GITHUB_APP_PRIVATE_KEY")
        return None

    # Get installation ID
    installation_id = get_installation_id()
    if not installation_id:
        logger.error("Could not determine installation ID")
        return None

    # Generate JWT
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + 600,  # 10 minutes
        'iss': APP_ID
    }

    try:
        # Create JWT
        encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256')

        # Get installation access token
        headers = {
            'Authorization': f'Bearer {encoded_jwt}',
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.post(
            f'https://api.github.com/app/installations/{installation_id}/access_tokens',
            headers=headers
        )

        if response.status_code == 201:
            return response.json()['token']
        else:
            logger.error(f"Failed to get installation token: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error getting GitHub App token: {e}")
        return None
