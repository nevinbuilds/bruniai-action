import os
import sys
import pytest

# Add the project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Set the asyncio default fixture loop scope explicitly to function
pytest.asyncio_default_fixture_loop_scope = "function"
