# Visual Regression Testing with Playwright and OpenAI

This GitHub Action automates visual regression testing by comparing screenshots and highlighting differences between production and pull request versions. It's perfect for CI/CD pipelines, helping teams catch unintended visual changes in web applications, design systems, and UI-driven projects.

## Quick Start

Add this to your workflow file (`.github/workflows/visual-regression.yml`):

```yaml
name: Visual Regression Test
on:
  pull_request:
    branches: [main]

jobs:
  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Visual Regression Test
        uses: ./
        with:
          base-url: "https://www.example.com/"
          # Update to your preview URL format.
          pr-url: "https://example-git-${{ steps.branch-name.outputs.branch_name }}-{{github.actor}}.vercel.app"
```

## Features

- Automated screenshot comparison
- AI-powered analysis of visual changes
- GitHub PR integration
- Detailed reporting
- Easy CI/CD integration

## Documentation

- [Getting Started](docs/getting-started.md) - Local development setup
- [Configuration Guide](docs/configuration.md) - Configuration options
- [Usage Examples](docs/usage-examples.md) - Common use cases
- [Architecture](docs/architecture.md) - System overview
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Contributing](docs/contributing.md) - How to contribute

## Requirements

- GitHub repository
- OpenAI API key (set as `OPENAI_API_KEY` secret in your repository)

## License

[Add your license here]
