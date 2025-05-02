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
        uses: nevinbuilds/bruniai-action@v1.11
        with:
          # Your production URL.
          base-url: "https://www.example.com/"
          # Update to your preview URL format.
          pr-url: "https://example-git-${{ steps.branch-name.outputs.branch_name }}-{{github.actor}}.vercel.app"
```

### Preview URL format

The preview URL format depends on your deployment platform. Here are the common formats:

#### Vercel Preview URLs

Vercel automatically creates preview deployments for pull requests. The URL format is:

```
https://[project-name]-git-[branch-name]-[username].vercel.app
```

Example:

```yaml
pr-url: "https://myapp-git-${{ github.head_ref }}-myusername.vercel.app"
```

#### Netlify Preview URLs

Netlify creates preview deployments with the following format:

```
https://deploy-preview-[PR-number]--[site-name].netlify.app
```

Example:

```yaml
pr-url: "https://deploy-preview-${{ github.event.pull_request.number }}--myapp.netlify.app"
```

#### Finding Your Preview URL Format

1. **For Vercel**:

   - Go to your Vercel dashboard
   - Click on your project
   - Look at the preview deployment URLs for recent PRs
   - The format will be consistent across all preview deployments

2. **For Netlify**:
   - Go to your Netlify dashboard
   - Click on your site
   - Look at the "Deploy previews" section
   - The URL format will follow the pattern shown above

#### Custom Domains

If you're using custom domains, replace the platform-specific domain with your custom domain while keeping the preview-specific parts of the URL.

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
