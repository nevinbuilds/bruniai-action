# Running Tests

Follow these steps to run the test suite locally.

## Prerequisites

- Python 3.10 (or use the bundled virtualenv `venv310`).
- macOS/Linux shell commands shown; adapt as needed for Windows.

## Option A: Use the bundled virtual environment

```bash
# From repo root
source venv310/bin/activate

# Ensure package is installed for imports like `src.*`
pip install -e .

# Run all tests
PYTHONPATH=$PWD pytest -q

# Run a specific test file
PYTHONPATH=$PWD pytest -q tests/unit/test_pr_comments.py

# Run by keyword
PYTHONPATH=$PWD pytest -q -k pr_comments
```

## Option B: Create a fresh virtual environment

```bash
# From repo root
python3 -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -r requirements-dev.txt
pip install -e .

PYTHONPATH=$PWD pytest -q
```

## Notes

- If you see `ModuleNotFoundError: No module named 'src'`, ensure you:
  - Installed the package in editable mode: `pip install -e .`, and
  - Set `PYTHONPATH=$PWD` when running pytest.
- To stop on first failure, add `-x`.
- To increase verbosity, omit `-q` or add `-vv`.
- Coverage is configured via `pytest.ini`; you can add `--cov` flags if desired.
