# Configuration Guide

This guide explains how to configure the Visual Regression Testing tool to suit your specific needs.

## Environment Variables

The following environment variables can be set in your `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

## Command Line Arguments

The main script accepts the following arguments:

```bash
python3 -m src.runner --base-url <production-url> --pr-url <pull-request-url>
```

### Required Arguments

- `--base-url`: The URL of the production version to compare against
- `--pr-url`: The URL of the pull request version to test

## GitHub Action Configuration

The GitHub Action can be configured in your workflow file:

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
          base-url: ${{ github.event.pull_request.base.ref }}
          pr-url: ${{ github.event.pull_request.head.ref }}

        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Best Practices

1. **URL Selection**

   - Use stable production URLs
   - Ensure PR URLs are accessible
   - Test with different page types

2. **Output Management**
   - Regularly clean up old output files
   - Store important baselines
   - Archive significant changes

## Troubleshooting Configuration

If you encounter issues:

1. Check your environment variables
2. Ensure URLs are accessible
3. Verify GitHub token permissions

For more help, see the [Troubleshooting Guide](troubleshooting.md).
