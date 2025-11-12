# Usage Examples

This document provides practical examples of how to use the Visual Regression Testing tool in different scenarios.

## Basic Usage

### Running a Simple Comparison

```bash
node dist/index.js \
  --base-url https://www.example.com \
  --pr-url https://pr-example.com
```

Or for development:

```bash
npm run dev -- \
  --base-url https://www.example.com \
  --pr-url https://pr-example.com
```

### Testing Multiple Pages

```bash
node dist/index.js \
  --base-url https://www.example.com \
  --pr-url https://pr-example.com \
  --pages "/,/about,/contact,/pricing"
```

**Note**: When running locally, use comma-separated format for pages. In GitHub Actions, use JSON array format: `'["/", "/about", "/contact", "/pricing"]'`

## GitHub Actions Integration

### Basic Workflow

```yaml
name: Visual Regression Test
on:
  pull_request:
    branches: [main]

jobs:
  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Visual Regression Test
        uses: ./
        with:
          # Your production URL.
          base-url: "https://www.example.com/"
          # Update to your preview URL format.
          pr-url: "https://example-git-${{ github.head_ref }}-${{ github.actor }}.vercel.app"

        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Multi-Page Testing Workflow

```yaml
name: Visual Regression Test
on:
  pull_request:
    branches: [main]

jobs:
  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Visual Regression Test
        uses: ./
        with:
          base-url: "https://www.example.com/"
          pr-url: "https://example-git-${{ github.head_ref }}-${{ github.actor }}.vercel.app"
          pages: '["/", "/about", "/contact", "/pricing"]'

        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Common Use Cases

### 1. Component Testing

Test specific components or sections of your website:

```bash
node dist/index.js \
  --base-url https://www.example.com/components/button \
  --pr-url https://pr-example.com/components/button
```

### 2. Design System Testing

Test your design system components:

```bash
node dist/index.js \
  --base-url https://design.example.com \
  --pr-url https://pr-design.example.com
```

### 3. E-commerce Site Testing

Test critical pages for an e-commerce site:

```yaml
name: E-commerce Visual Test
on:
  pull_request:
    branches: [main]

jobs:
  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Visual Regression Test
        uses: ./
        with:
          base-url: "https://shop.example.com/"
          pr-url: "https://shop-git-${{ github.head_ref }}-myusername.vercel.app"
          pages: '["/", "/products", "/cart", "/checkout", "/account"]'

        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### 4. Marketing Site Testing

Test key marketing pages:

```yaml
name: Marketing Site Visual Test
on:
  pull_request:
    branches: [main]

jobs:
  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Visual Regression Test
        uses: ./
        with:
          base-url: "https://marketing.example.com/"
          pr-url: "https://marketing-git-${{ github.head_ref }}-myusername.vercel.app"
          pages: '["/", "/features", "/pricing", "/contact", "/blog"]'

        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Tips and Tricks

1. **Selective Testing**

   - Focus on critical paths first
   - Test components individually
   - Use specific URLs for targeted testing

2. **Multi-Page Testing**

   - Start with the most important pages
   - Test pages that are frequently updated
   - Consider user journey flows
   - Balance coverage with execution time

3. **Performance Optimization**

   - Test during off-peak hours
   - Clean up old test results
   - Limit the number of pages for faster feedback

4. **Integration with CI/CD**
   - Configure notifications
   - Handle test failures gracefully
   - Use conditional testing based on file changes

For more detailed information, refer to the [Configuration Guide](configuration.md).
