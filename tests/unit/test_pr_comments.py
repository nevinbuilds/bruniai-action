import pytest
from unittest.mock import patch, mock_open
from src.github.pr_comments import post_pr_comment, get_pr_number_from_event

def test_post_pr_comment_update_existing():
    # Mock requests.get to return a fake response with an existing comment
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"id": 1, "body": "Information about visual testing analysis provided by [bruniai]"}]
        # Mock requests.patch to simulate updating the comment
        with patch("requests.patch") as mock_patch:
            mock_patch.return_value.status_code = 200
            # Mock get_github_app_token to return a fake token
            with patch("src.github.pr_comments.get_github_app_token", return_value="fake_token"):
                # Mock os.getenv to return fake repo, PR number, and run ID
                with patch("os.getenv", side_effect=lambda key: {"GITHUB_REPOSITORY": "org/repo", "PR_NUMBER": "123", "GITHUB_RUN_ID": "456"}.get(key)):
                    post_pr_comment("Updated summary")
                    mock_patch.assert_called_once()

def test_get_pr_number_from_event_success():
    # Mock os.getenv to return a fake event path
    with patch("os.getenv", side_effect=lambda key: {"GITHUB_EVENT_PATH": "/fake/path", "GITHUB_REPOSITORY": "org/repo"}.get(key)):
        # Mock open to return a fake event JSON payload
        with patch("builtins.open", mock_open(read_data='{"pull_request": {"number": 123}}')):
            pr_number = get_pr_number_from_event()
            assert pr_number == 123
