import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from PIL import Image
import numpy as np
import sys

# Add the project root to sys.path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_agent import (
    generate_diff_image,
    take_screenshot_with_playwright,
    get_pr_number_from_event,
    post_pr_comment
)

@pytest.fixture
def sample_images():
    """Create sample test images for testing."""
    # Create test directory if it doesn't exist
    test_images_dir = os.path.join(os.path.dirname(__file__), 'test_images')
    os.makedirs(test_images_dir, exist_ok=True)

    # Define image paths
    img1_path = os.path.join(test_images_dir, 'test_image1.png')
    img2_path = os.path.join(test_images_dir, 'test_image2.png')
    diff_path = os.path.join(test_images_dir, 'test_diff.png')

    # Create a simple test image
    img1 = Image.new('RGB', (100, 100), color='white')
    img1.save(img1_path)

    # Create a second image with a slight difference
    img2 = Image.new('RGB', (100, 100), color='white')
    img2_pixels = img2.load()
    for i in range(10, 20):
        for j in range(10, 20):
            img2_pixels[i, j] = (255, 0, 0)  # Add a red square
    img2.save(img2_path)

    yield {'img1': img1_path, 'img2': img2_path, 'diff': diff_path}

    # Cleanup (uncomment if you want to delete the test images after tests)
    import shutil
    shutil.rmtree(test_images_dir)

def test_generate_diff_image(sample_images):
    """Test that diff image generation works correctly."""
    generate_diff_image(sample_images['img1'], sample_images['img2'], sample_images['diff'])

    # Verify the diff image was created
    assert os.path.exists(sample_images['diff'])

    # Verify the diff contains the expected changes
    diff_img = Image.open(sample_images['diff'])
    diff_array = np.array(diff_img)

    # Check that there are red pixels in the diff image
    assert np.any(diff_array[:, :, 0] == 255)

@patch('subprocess.run')
def test_take_screenshot_with_playwright_success(mock_run):
    """Test successful screenshot capture."""
    mock_run.return_value = MagicMock(returncode=0)

    result = take_screenshot_with_playwright('http://example.com', 'output.png')

    assert result is True
    mock_run.assert_called_once()

@patch('subprocess.run')
def test_take_screenshot_with_playwright_failure(mock_run):
    """Test failed screenshot capture."""
    mock_run.side_effect = Exception("Playwright failed")

    result = take_screenshot_with_playwright('http://example.com', 'output.png')

    assert result is False
    mock_run.assert_called_once()

@patch('os.path.exists')
@patch('builtins.open')
@patch('os.getenv')
def test_get_pr_number_from_event(mock_getenv, mock_open, mock_exists):
    """Test getting PR number from event file."""
    # Mock the GITHUB_EVENT_PATH environment variable
    mock_getenv.return_value = '/path/to/event.json'
    mock_exists.return_value = True
    mock_open.return_value.__enter__.return_value.read.return_value = '{"pull_request": {"number": 42}}'

    # Patch to simulate the json.load() behavior
    with patch('json.load', return_value={"pull_request": {"number": 42}}):
        pr_number = get_pr_number_from_event()

    assert pr_number == 42

@patch('requests.post')
@patch('os.getenv')
def test_post_pr_comment(mock_getenv, mock_post):
    """Test posting PR comment."""
    # Set up environment variables
    mock_getenv.side_effect = lambda key, default=None: {
        'GITHUB_TOKEN': 'fake_token',
        'GITHUB_REPOSITORY': 'org/repo',
        'PR_NUMBER': '123'
    }.get(key, default)

    # Mock successful response
    mock_post.return_value.status_code = 201

    post_pr_comment("Test comment")

    # Verify the POST was made with correct parameters
    mock_post.assert_called_once_with(
        'https://api.github.com/repos/org/repo/issues/123/comments',
        json={'body': 'Test comment'},
        headers={
            'Authorization': 'token fake_token',
            'Accept': 'application/vnd.github.v3+json'
        }
    )

# Test async functionality would require more complex mocking of the OpenAI API
# Here's a simple test for demonstration
@pytest.mark.asyncio
async def test_run_comparison_mock():
    """Test the comparison function with mocks."""
    with patch('scripts.run_agent.Runner') as mock_runner:
        # Setup the mock
        mock_result = MagicMock()
        mock_result.final_output = "Comparison result"
        mock_runner.run = AsyncMock(return_value=mock_result)

        # Call the function under test
        from scripts.run_agent import run_comparison
        mcp_server = MagicMock()
        agent = MagicMock()
        prompt = "Test prompt"

        result = await run_comparison(mcp_server, agent, prompt)

        # Assertions
        assert result == "Comparison result"
        mock_runner.run.assert_awaited_once_with(agent, prompt)
