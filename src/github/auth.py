import os
import jwt
import time
import requests
import logging

logger = logging.getLogger("agent-runner")

# Hardcoded App ID
APP_ID = "1239933"

def get_github_app_token():
    """Get a GitHub App installation access token."""
    # Get the private key from the GitHub token
    private_key = os.getenv("GITHUB_TOKEN")
    if not private_key:
        logger.error("Missing GITHUB_TOKEN")
        return None

    installation_id = os.getenv("GITHUB_INSTALLATION_ID")
    if not installation_id:
        logger.error("Missing GITHUB_INSTALLATION_ID")
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
