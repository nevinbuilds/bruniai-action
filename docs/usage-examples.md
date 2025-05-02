# Usage Examples

This document provides practical examples of how to use the Visual Regression Testing tool in different scenarios.

## Basic Usage

### Running a Simple Comparison

```bash
python3 -m src.runner \
  --base-url https://www.example.com \
  --pr-url https://pr-example.com
```

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
      - uses: actions/checkout@v2
      - name: Run Visual Regression Test
        uses: ./
        with:
          base-url: ${{ github.event.pull_request.base.ref }}
          pr-url: ${{ github.event.pull_request.head.ref }}
```

## Common Use Cases

### 1. Component Testing

Test specific components or sections of your website:

```bash
python3 -m src.runner \
  --base-url https://www.example.com/components/button \
  --pr-url https://pr-example.com/components/button
```

### 2. Design System Testing

Test your design system components:

```bash
python3 -m src.runner \
  --base-url https://design.example.com \
  --pr-url https://pr-design.example.com
```

## Output Examples

### Successful Test Output

```
Visual Regression Test Results
=============================
Base URL: https://www.example.com
PR URL: https://pr-example.com

AI Analysis:
- No significant visual changes detected
- Minor layout adjustments within acceptable range
```

### Failed Test Output

```
Visual Regression Test Results
=============================
Base URL: https://www.example.com
PR URL: https://pr-example.com

AI Analysis:
- Significant layout changes detected in header
- Color scheme modifications in navigation
- New elements added to sidebar
```

## Tips and Tricks

1. **Selective Testing**

   - Focus on critical paths first
   - Test components individually
   - Use specific URLs for targeted testing

2. **Performance Optimization**

   - Test during off-peak hours
   - Clean up old test results

3. **Integration with CI/CD**
   - Configure notifications
   - Handle test failures gracefully

For more detailed information, refer to the [Configuration Guide](configuration.md).
