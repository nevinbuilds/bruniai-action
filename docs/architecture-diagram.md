# BruniAI Architecture Diagram

## TypeScript Application Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                          │
│  (action.yml - Composite Action)                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: Setup & Installation                                       │
│  - Setup Node.js 20+                                                │
│  - Install dependencies (npm install)                               │
│  - Build TypeScript (npm run build)                                 │
│  - Install Playwright browsers (for Stagehand)                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Main Runner (src/index.ts)                                │
│                                                                      │
│  Input:                                                              │
│  - base-url: Production/staging URL                                 │
│  - pr-url: Preview deployment URL                                   │
│  - pages: Comma-separated paths (e.g., "/,/about")                  │
│  - bruni-token: Optional API token                                  │
│  - bruni-api-url: Optional API URL                                   │
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
│  Step 3: Initialize Stagehand                                      │
│  (src/index.ts)                                                    │
│  - Initialize Stagehand browser automation                          │
│  - Set up browser context                                           │
│  - Configure viewport size                                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Fetch PR Metadata                                          │
│  (src/github/pr-metadata.ts)                                        │
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
│  │     (src/index.ts - Stagehand)                                │  │
│  │     - base_screenshot: Full page screenshot of base URL      │  │
│  │     - pr_screenshot: Full page screenshot of PR URL           │  │
│  │     - Uses: Stagehand browser automation                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5b. Generate Diff Image                                       │  │
│  │     (src/diff/diff.ts)                                        │  │
│  │     - Compare base and PR images                              │  │
│  │     - Create diff image with pixelmatch                        │  │
│  │     - Save diff image                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5c. Analyze Sections                                          │  │
│  │     (src/sections/sections.ts)                                │  │
│  │     - Analyze DOM structure side-by-side                      │  │
│  │     - Extract section information                              │  │
│  │     - Returns sections analysis text                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5d. Extract Section Bounding Boxes                            │  │
│  │     (src/sections/sectionExtraction.ts)                       │  │
│  │     - Extract DOM elements with bounding boxes                │  │
│  │     - Match sections with IDs                                 │  │
│  │     - Return sections with metadata                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 5e. Capture Section Screenshots                                │  │
│  │     (src/sections/sectionExtraction.ts)                       │  │
│  │     - Take screenshots of each section                         │  │
│  │     - Save base and PR section screenshots                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Store page_result with:                                            │
│  - page_path, base_url, pr_url                                       │
│  - base_screenshot, pr_screenshot, diff_output_path                 │
│  - section_screenshots                                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: Visual Analysis with GPT-4 Vision                         │
│  (src/vision/index.ts)                                              │
│  - Encode images to base64                                          │
│  - Call GPT-4 Vision API                                            │
│  - Analyze:                                                          │
│    • Missing sections (critical)                                    │
│    • Structural changes                                             │
│    • Visual changes                                                 │
│    • Layout issues                                                  │
│  - Returns: Structured JSON report                                   │
│                                                                      │
│  Store page_analysis with:                                          │
│  - page_path                                                         │
│  - sections_analysis                                                │
│  - visual_analysis (JSON)                                            │
│  - section_screenshots                                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 7: Generate Multi-Page Report                                 │
│  (src/reporter/report-generator.ts)                                 │
│  - Combine all page analyses                                         │
│  - Format markdown summary                                           │
│  - Determine overall status (pass/fail/warning)                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 8: Send Report to Bruni API (Optional)                       │
│  (src/reporter/reporter.ts)                                         │
│  - Compress images (WEBP, base64)                                   │
│  - Send to bruniai-app.vercel.app/api/tests                         │
│  - Get report URL for PR comment                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 9: Post PR Comment                                            │
│  (src/github/pr-comments.ts)                                        │
│  - Format markdown report                                            │
│  - Find/update existing comment or create new                       │
│  - Include report URL if available                                  │
│  - Include artifact links                                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 10: Cleanup                                                   │
│  - Close Stagehand browser                                           │
│  - Clean up temporary files                                          │
└─────────────────────────────────────────────────────────────────────┘

## Key Components

### 1. Screenshot Capture
- **Tool**: Stagehand (@browserbasehq/stagehand)
- **Output**: Full-page PNG screenshots
- **Location**: `images/` directory
- **Method**: AI-powered browser automation via Stagehand (which uses Playwright under the hood)

### 2. Section Analysis
- **Tool**: Stagehand + AI (GPT-4)
- **Method**: AI analyzes DOM structure side-by-side
- **Output**: Text description of sections with IDs, classes, attributes
- **Implementation**: `src/sections/sections.ts`

### 3. Visual Analysis
- **Tool**: OpenAI GPT-4 Vision API
- **Input**: Base64-encoded images (base, PR, diff)
- **Output**: Structured JSON with:
  - Status (pass/fail/warning)
  - Critical issues (missing sections)
  - Visual changes
  - Structural analysis
  - Recommendations
- **Implementation**: `src/vision/index.ts`

### 4. Image Processing
- **Diff Generation**: pixelmatch library
- **Compression**: Sharp library with WEBP format
- **Resizing**: Maintain aspect ratio, max dimensions
- **Implementation**: `src/diff/diff.ts`, `src/reporter/image-compression.ts`

### 5. GitHub Integration
- **Authentication**: GITHUB_TOKEN from environment
- **API**: GitHub REST API v3 (via @octokit/rest)
- **Actions**: Post/update PR comments
- **Implementation**: `src/github/pr-comments.ts`, `src/github/pr-metadata.ts`

### 6. Browser Automation
- **Tool**: Stagehand (@browserbasehq/stagehand)
- **Purpose**: Browser automation and DOM interaction
- **Features**: AI-powered browser control, screenshot capture

## Data Flow

```

Input URLs
│
├─► Screenshots (Stagehand)
│ │
│ ├─► Full Page Images
│ └─► Section Images
│
├─► DOM Analysis (Stagehand)
│ └─► Section Bounding Boxes
│
└─► AI Analysis
│
├─► Section Structure (Stagehand + GPT-4)
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
2. **GitHub API**: PR comments and metadata (via @octokit/rest)
3. **Stagehand**: @browserbasehq/stagehand for AI-powered browser automation (uses Playwright browsers under the hood)
4. **Bruni API**: External reporting service (optional)
5. **Sharp**: Image processing and compression
6. **pixelmatch**: Image diff generation

## File Structure

```

src/
├── index.ts # Main entry point
├── args.ts # Command-line argument parsing
├── diff/
│ └── diff.ts # Diff image generation
├── sections/
│ ├── sections.ts # Section structure analysis
│ ├── sectionExtraction.ts # Section extraction and screenshots
│ └── sectionDom.ts # DOM utilities
├── vision/
│ ├── index.ts # GPT-4 Vision analysis entry
│ ├── vision.ts # Vision API client
│ ├── types.ts # Vision analysis types
│ └── utils.ts # Vision utilities
├── github/
│ ├── pr-comments.ts # PR comment posting
│ ├── pr-metadata.ts # PR metadata fetching
│ └── auth.ts # GitHub authentication
├── reporter/
│ ├── index.ts # Reporter exports
│ ├── reporter.ts # Bruni API client
│ ├── report-generator.ts # Report formatting
│ ├── image-compression.ts # Image compression/encoding
│ └── types.ts # Type definitions
└── utils/
└── window.ts # Viewport utilities

```

```
