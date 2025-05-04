import os
import json
import jwt
import time
import requests
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("agent-runner")

# Hardcoded App ID
APP_ID = "1239933"

def get_installation_id():
    """Get the installation ID from the event payload."""
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        logger.error("Missing GITHUB_EVENT_PATH")
        return None

    try:
        with open(event_path, 'r') as f:
            event = json.load(f)
            # Log the event payload for debugging
            logger.info("Event payload:")
            logger.info(json.dumps(event, indent=2))

            # Try different possible locations for the installation ID
            installation_id = (
                event.get("installation", {}).get("id") or
                event.get("repository", {}).get("installation_id") or
                event.get("pull_request", {}).get("head", {}).get("repo", {}).get("owner", {}).get("id")
            )
            if installation_id:
                logger.info(f"Found installation ID: {installation_id}")
                return str(installation_id)
            logger.error("Installation ID not found in event payload")
            return None
    except Exception as e:
        logger.error(f"Error reading installation ID from event: {e}")
        return None

def get_github_app_token():
    """Get a GitHub App installation access token."""
    # Get the private key from the environment
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    if not private_key:
        logger.error("Missing GITHUB_APP_PRIVATE_KEY")
        return None

    try:
        # Load the private key using cryptography
        key = serialization.load_pem_private_key(
            private_key.encode('utf-8'),
            password=None,
            backend=default_backend()
        )

        # Get installation ID from the event payload
        installation_id = get_installation_id()
        if not installation_id:
            logger.error("Could not determine installation ID")
            return None

        # Generate JWT as shown in GitHub docs
        payload = {
            'iat': int(time.time()),
            'exp': int(time.time()) + 600,  # 10 minutes
            'iss': APP_ID
        }

        # Create JWT using the loaded private key
        encoded_jwt = jwt.encode(payload, key, algorithm='RS256')

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
