# Testing Guide

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt -r requirements-dev.txt
   ```

## Running Tests

- Run all tests:
  ```bash
  pytest
  ```
- Run a specific test file:
  ```bash
  pytest tests/unit/test_types.py
  ```

## Coverage

- Run tests with coverage report:
  ```bash
  pytest --cov=src --cov-report=term-missing
  ```
- Generate an HTML coverage report:
  ```bash
  pytest --cov=src --cov-report=html
  open htmlcov/index.html
  ```

## Adding New Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Name test files as `test_*.py`
- Use `pytest` conventions for test functions/classes

## CI

Tests are automatically run on GitHub Actions for every push and pull request to `main`.
