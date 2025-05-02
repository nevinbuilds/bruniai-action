# Architecture Overview

This document provides a high-level overview of the system architecture and its components.

## System Components

### 1. Core Components

- **Playwright Integration**

  - Handles browser automation
  - Captures screenshots of web pages
  - Manages different viewports and devices

- **Image Processing**

  - Compares screenshots between versions
  - Highlights visual differences
  - Calculates similarity metrics

- **AI Analysis**
  - Uses OpenAI to analyze visual changes
  - Provides intelligent insights about differences
  - Helps prioritize important changes

### 2. Directory Structure

```
src/
├── core/           # Core functionality and utilities
├── playwright_utils/  # Playwright-specific implementations
├── runner/        # Test execution and orchestration
├── github/        # GitHub integration and actions
├── image_processing/  # Image comparison and processing
└── analysis/      # AI-powered analysis components
```

## Workflow

1. **Initialization**

   - Load configuration
   - Set up Playwright
   - Initialize AI services

2. **Capture Phase**

   - Navigate to specified URLs
   - Capture screenshots at different viewports
   - Store images for comparison

3. **Comparison Phase**

   - Process captured images
   - Identify visual differences
   - Generate difference maps

4. **Analysis Phase**

   - Send differences to AI for analysis
   - Generate human-readable reports
   - Create visualizations of changes

5. **Reporting Phase**
   - Generate detailed reports
   - Update GitHub status
   - Provide actionable feedback

## Integration Points

### GitHub Actions

- Triggers on pull requests
- Updates PR status
- Posts comments with findings

### OpenAI Integration

- Processes visual differences
- Provides context-aware analysis
- Generates human-readable reports

## Data Flow

1. User triggers test via GitHub Action
2. System captures production and PR screenshots
3. Images are processed and compared
4. Differences are analyzed by AI
5. Results are reported back to GitHub

## Security Considerations

- API keys are stored securely
- Screenshots are processed locally
- No sensitive data is stored
- Temporary files are cleaned up

## Performance Considerations

- Parallel screenshot capture
- Efficient image processing
- Caching of intermediate results
- Optimized AI API usage
