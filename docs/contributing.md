# Contributing Guide

Thank you for your interest in contributing to the Visual Regression Testing project! This guide will help you get started with contributing.

## Development Setup

1. **Fork the Repository**

   - Create a fork of the main repository
   - Clone your fork locally

2. **Set Up Development Environment**

   ```bash
   # Create and activate virtual environment
   python3.10 -m venv venv310
   source venv310/bin/activate  # On Windows: venv310\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Install Playwright MCP
   npm install -g @playwright/mcp
   ```

3. **Run Tests**
   ```bash
   pytest tests/
   ```

## Contribution Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for all public functions
- Keep functions focused and small
- Write unit tests for new features

### Git Workflow

1. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**

   - Write clear commit messages
   - Keep commits focused and atomic
   - Reference issues in commit messages

3. **Push Your Changes**

   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request**
   - Fill out the PR template
   - Reference related issues
   - Request reviews from maintainers

### Documentation

- Update documentation for new features
- Add examples where appropriate
- Keep documentation in sync with code
- Use clear and concise language

## Issue Reporting

When reporting issues:

1. **Bug Reports**

   - Describe the problem
   - Provide steps to reproduce
   - Include error messages
   - Specify environment details

2. **Feature Requests**
   - Describe the feature
   - Explain the use case
   - Suggest implementation
   - Consider alternatives

## Community Guidelines

1. **Be Respectful**

   - Use inclusive language
   - Be patient with others
   - Value different perspectives

2. **Be Helpful**

   - Answer questions
   - Share knowledge
   - Guide new contributors

3. **Be Professional**
   - Stay on topic
   - Be constructive
   - Follow the code of conduct

## Getting Help

If you need help:

1. Check the documentation
2. Search existing issues
3. Ask in the community chat
4. Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the project's license.
