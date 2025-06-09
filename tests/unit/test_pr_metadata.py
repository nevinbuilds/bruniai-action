import pytest
from unittest.mock import patch
from src.github.pr_metadata import fetch_pr_metadata

def test_fetch_pr_metadata_success():
    # Mock requests.get to return a fake response
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"title": "Test PR", "body": "Test body"}
        # Mock get_github_app_token to return a fake token
        with patch("src.github.pr_metadata.get_github_app_token", return_value="fake_token"):
            # Mock os.getenv to return fake repo and PR number
            with patch("os.getenv", side_effect=lambda key: {"GITHUB_REPOSITORY": "org/repo", "PR_NUMBER": "123"}.get(key)):
                title, body = fetch_pr_metadata()
                assert title == "Test PR"
                assert body == "Test body"
