# BruniAI Architecture Diagram

## Current Python Application Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                          │
│  (action.yml - Composite Action)                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: Setup & Installation                                       │
│  - Setup Node.js & Python                                           │
│  - Install dependencies (pip, npm)                                 │
│  - Install Playwright browsers                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Start MCP Server                                           │
│  - Start @playwright/mcp on port 8931                              │
│  - Wait for server to be ready                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Main Runner (src/runner/__main__.py)                       │
│                                                                      │
│  Input:                                                              │
│  - base-url: Production/staging URL                                 │
│  - pr-url: Preview deployment URL                                   │
│  - pages: JSON array of paths (e.g., ["/", "/about"])               │
│  - bruni-token: Optional API token                                  │
│                                                                      │
│  Environment:                                                        │
│  - OPENAI_API_KEY: For GPT-4 Vision                                 │
│  - GITHUB_TOKEN: For PR comments                                    │
│  - GITHUB_REPOSITORY: Repo identifier                               │
│  - PR_NUMBER: Pull request number                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Fetch PR Metadata                                          │
│  (src/github/pr_metadata.py)                                        │
│  - PR title                                                          │
│  - PR description                                                    │
│  - Repository info                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Process Each Page (Loop)                                   │
│                                                                      │
│  For each page_path in pages:                                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5a. Take Screenshots                                          │  │
│  │     (src/playwright_utils/screenshot.py)                      │  │
│  │     - base_screenshot: Full page screenshot of base URL      │  │
│  │     - pr_screenshot: Full page screenshot of PR URL           │  │
│  │     - Uses: npx playwright screenshot                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5b. Extract Section Bounding Boxes                            │  │
│  │     (src/playwright_utils/bounding_boxes.py)                  │  │
│  │     - Extract DOM elements with bounding boxes                │  │
│  │     - Save sections JSON                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5c. Generate Diff Image                                       │  │
│  │     (src/image_processing/diff.py)                            │  │
│  │     - Compare base and PR images                              │  │
│  │     - Create diff image with red highlights                   │  │
│  │     - Save resized versions                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Store page_result with:                                            │
│  - page_path, base_url, pr_url                                       │
│  - base_screenshot, pr_screenshot, diff_output_path                 │
│  - sections data                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: MCP Server Context (managed_mcp_server)                   │
│  (src/core/mcp.py)                                                  │
│  - Connect to MCP server at localhost:8931                         │
│  - Retry logic with exponential backoff                              │
│  - Timeout handling                                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 7: Analyze Each Page (Loop)                                   │
│                                                                      │
│  For each page_result:                                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 7a. Section Analysis                                           │  │
│  │     (src/analysis/sections.py)                                │  │
│  │     - Use MCP server with Agent                               │  │
│  │     - Extract real DOM info via Playwright                    │  │
│  │     - Analyze base URL structure                               │  │
│  │     - Identify sections with IDs, classes, IDs                │  │
│  │     - Detect animations                                        │  │
│  │     - Returns: sections_analysis (text)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 7b. Extract Sections with IDs                                 │  │
│  │     (src/playwright_utils/bounding_boxes.py)                  │  │
│  │     - Match sections from analysis                             │  │
│  │     - Enrich with section IDs                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 7c. Capture Section Screenshots                                │  │
│  │     (src/playwright_utils/screenshot.py)                      │  │
│  │     - For each section: base and PR screenshots               │  │
│  │     - Uses CSS selectors from analysis                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 7d. Visual Analysis with GPT-4 Vision                         │  │
│  │     (src/analysis/vision.py)                                  │  │
│  │     - Encode images to base64                                 │  │
│  │     - Call GPT-4.1-mini Vision API                             │  │
│  │     - Analyze:                                                │  │
│  │       • Missing sections (critical)                            │  │
│  │       • Structural changes                                     │  │
│  │       • Visual changes                                         │  │
│  │       • Layout issues                                          │  │
│  │     - Returns: Structured JSON report                          │  │
│  │     - Rate limiting via decorator                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Store page_analysis with:                                           │
│  - page_path                                                         │
│  - sections_analysis                                                 │
│  - visual_analysis (JSON)                                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 8: Generate Multi-Page Report                                 │
│  (src/reporter/report_generator.py)                                  │
│  - Combine all page analyses                                         │
│  - Format markdown summary                                           │
│  - Determine overall status (pass/fail/warning)                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 9: Send Report to Bruni API (Optional)                       │
│  (src/reporter/reporter.py)                                         │
│  - Compress images (WEBP, base64)                                   │
│  - Send to bruniai-app.vercel.app/api/tests                         │
│  - Get report URL for PR comment                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 10: Post PR Comment                                           │
│  (src/github/pr_comments.py)                                        │
│  - Format markdown report                                            │
│  - Find/update existing comment or create new                       │
│  - Include report URL if available                                  │
│  - Include artifact links                                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 11: Cleanup                                                   │
│  - Stop MCP server                                                   │
│  - Clean up temporary files                                          │
└─────────────────────────────────────────────────────────────────────┘

## Key Components

### 1. Screenshot Capture
- **Tool**: Playwright CLI (npx playwright screenshot)
- **Output**: Full-page PNG screenshots
- **Location**: `images/` directory

### 2. Section Analysis
- **Tool**: MCP Server + Agents framework
- **Method**: AI agent analyzes DOM structure
- **Output**: Text description of sections with IDs, classes, attributes

### 3. Visual Analysis
- **Tool**: OpenAI GPT-4.1-mini Vision API
- **Input**: Base64-encoded images (base, PR, diff)
- **Output**: Structured JSON with:
  - Status (pass/fail/warning)
  - Critical issues (missing sections)
  - Visual changes
  - Structural analysis
  - Recommendations

### 4. Image Processing
- **Diff Generation**: PIL/Pillow (ImageChops.difference)
- **Compression**: PIL with WEBP format
- **Resizing**: Maintain aspect ratio, max dimensions

### 5. GitHub Integration
- **Authentication**: GITHUB_TOKEN from environment
- **API**: GitHub REST API v3
- **Actions**: Post/update PR comments

### 6. Rate Limiting
- **Implementation**: Decorator-based (20 calls/min)
- **Purpose**: Prevent API throttling

## Data Flow

```

Input URLs
│
├─► Screenshots (Playwright)
│ │
│ ├─► Full Page Images
│ └─► Section Images
│
├─► DOM Analysis (Playwright)
│ └─► Section Bounding Boxes
│
└─► AI Analysis
│
├─► Section Structure (MCP + Agents)
│ └─► Text Analysis
│
└─► Visual Differences (GPT-4 Vision)
└─► JSON Report
│
├─► PR Comment (GitHub)
└─► API Report (Bruni)

```

## External Dependencies

1. **OpenAI API**: GPT-4 Vision for image analysis
2. **GitHub API**: PR comments and metadata
3. **MCP Server**: @playwright/mcp for browser automation via agents
4. **Bruni API**: External reporting service (optional)
5. **Playwright**: Browser automation and screenshots

## File Structure

```

src/
├── runner/
│ └── **main**.py # Main entry point
├── playwright_utils/
│ ├── screenshot.py # Screenshot capture
│ ├── bounding_boxes.py # Section extraction
│ └── css_utils.py # CSS selector utilities
├── analysis/
│ ├── vision.py # GPT-4 Vision analysis
│ └── sections.py # Section structure analysis
├── image_processing/
│ ├── diff.py # Diff image generation
│ └── compression.py # Image compression/encoding
├── github/
│ ├── pr_comments.py # PR comment posting
│ ├── pr_metadata.py # PR metadata fetching
│ └── auth.py # GitHub authentication
├── reporter/
│ ├── reporter.py # Bruni API client
│ ├── report_generator.py # Report formatting
│ └── types.py # Type definitions
└── core/
├── mcp.py # MCP server management
└── rate_limit.py # Rate limiting decorator

```

```
