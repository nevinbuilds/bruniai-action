# Migration Plan: Python to TypeScript (Mastra.ai / useWorkflow)

## Executive Summary

This document outlines the migration strategy for converting the BruniAI visual regression testing tool from a Python-based script to a TypeScript-based workflow orchestration system using either **Mastra.ai** or **Vercel's useWorkflow** framework.

## Current State Analysis

### Technology Stack (Python)
- **Language**: Python 3.10+
- **Runtime**: Async Python (asyncio)
- **Browser Automation**: Playwright (via CLI)
- **AI Analysis**: OpenAI GPT-4 Vision API
- **Agent Framework**: Agents (Python) + MCP Server
- **Image Processing**: PIL/Pillow, NumPy
- **GitHub Integration**: requests library
- **Deployment**: GitHub Actions composite action

### Key Workflows Identified

1. **Screenshot Capture Workflow**
   - Sequential: base → pr → diff generation
   - Parallel potential: Multiple pages can be processed in parallel

2. **Section Analysis Workflow**
   - Sequential: Extract DOM → Analyze with MCP → Match sections
   - Can be parallelized per page

3. **Visual Analysis Workflow**
   - Sequential: Encode images → Call GPT-4 → Parse JSON
   - Rate-limited: 20 calls/minute

4. **Reporting Workflow**
   - Sequential: Format report → Post to API → Post PR comment
   - Optional: Bruni API submission

## Migration Options

### Option A: Mastra.ai
**Pros:**
- Framework designed for AI agent orchestration
- Built-in agent management
- Strong TypeScript support
- Good for complex multi-step AI workflows

**Cons:**
- Less mature ecosystem
- May require custom implementation for some features
- Less documentation/examples

### Option B: Vercel useWorkflow
**Pros:**
- Mature, production-ready framework
- Excellent observability and debugging
- Built-in retry and error handling
- Great TypeScript DX
- Active community and documentation
- Works with Next.js, Hono, Nitro, SvelteKit

**Cons:**
- Requires Vercel deployment (or self-hosting)
- May have vendor lock-in concerns (though open source)

**Recommendation**: **Vercel useWorkflow** for better maturity, observability, and production readiness.

## Migration Architecture

### Proposed TypeScript Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              GitHub Actions / Workflow Trigger               │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Workflow Entry Point (useWorkflow)                  │
│         - Receive: base-url, pr-url, pages                  │
│         - Validate inputs                                   │
│         - Initialize context                                │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Fetch PR Metadata (use step)                       │
│  - GitHub API call                                          │
│  - Extract title, description, PR number                    │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Process Pages (Parallel Workflow)                  │
│                                                                 │
│  For each page_path:                                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Sub-workflow: Analyze Page                            │   │
│  │  - Take screenshots (base + pr)                       │   │
│  │  - Extract sections                                    │   │
│  │  - Generate diff                                       │   │
│  │  - Analyze with AI                                     │   │
│  │  - Return page analysis                                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Aggregate Results (use step)                       │
│  - Combine all page analyses                                │
│  - Generate overall status                                  │
│  - Format markdown report                                   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Send Report (use step)                             │
│  - Compress images                                          │
│  - Send to Bruni API (if token provided)                    │
│  - Get report URL                                           │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Post PR Comment (use step)                         │
│  - Format markdown                                          │
│  - Find/update existing comment                             │
│  - Post to GitHub                                           │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Migration Plan

### Phase 1: Project Setup & Infrastructure

#### 1.1 Initialize TypeScript Project
```bash
# Create new TypeScript project
npm init -y
npm install -D typescript @types/node tsx
npm install workflow  # For useWorkflow
# OR
npm install @mastra/core  # For Mastra.ai

# Install dependencies
npm install playwright @playwright/test
npm install openai
npm install @octokit/rest
npm install sharp  # For image processing (replaces PIL)
npm install dotenv
```

#### 1.2 Project Structure
```
bruniai-ts/
├── src/
│   ├── workflows/
│   │   └── visual-regression.ts      # Main workflow
│   ├── steps/
│   │   ├── fetch-pr-metadata.ts
│   │   ├── take-screenshots.ts
│   │   ├── extract-sections.ts
│   │   ├── generate-diff.ts
│   │   ├── analyze-sections.ts
│   │   ├── analyze-visual.ts
│   │   ├── send-report.ts
│   │   └── post-pr-comment.ts
│   ├── utils/
│   │   ├── playwright.ts
│   │   ├── image-processing.ts
│   │   ├── github.ts
│   │   ├── rate-limiter.ts
│   │   └── types.ts
│   ├── services/
│   │   ├── mcp-server.ts
│   │   ├── openai-client.ts
│   │   └── bruni-api.ts
│   └── index.ts                      # Entry point
├── types/
│   └── workflow.ts                   # Workflow type definitions
├── package.json
├── tsconfig.json
└── .env.example
```

### Phase 2: Core Functionality Migration

#### 2.1 Type Definitions
**File**: `src/utils/types.ts`

```typescript
export interface WorkflowInput {
  baseUrl: string;
  prUrl: string;
  pages?: string[];
  bruniToken?: string;
  bruniApiUrl?: string;
}

export interface PageResult {
  pagePath: string;
  baseUrl: string;
  prUrl: string;
  baseScreenshot: string;  // Path or base64
  prScreenshot: string;
  diffImage: string;
  sections: Section[];
}

export interface Section {
  sectionId: string;
  name: string;
  htmlElement: string;
  htmlId?: string;
  htmlClasses?: string;
  ariaLabel?: string;
  boundingBox: BoundingBox;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface VisualAnalysis {
  id: string;
  status: 'pass' | 'fail' | 'warning' | 'none';
  criticalIssues: CriticalIssues;
  structuralAnalysis: StructuralAnalysis;
  visualChanges: VisualChanges;
  conclusion: Conclusion;
}

export interface PageAnalysis {
  pagePath: string;
  sectionsAnalysis: string;
  visualAnalysis: VisualAnalysis;
  sectionScreenshots: Record<string, {
    base: string;
    pr: string;
  }>;
}
```

#### 2.2 Playwright Utilities
**File**: `src/utils/playwright.ts`

Replace Python's `subprocess.run` with Playwright's Node.js API:

```typescript
import { chromium } from 'playwright';
import { writeFile } from 'fs/promises';

export async function takeScreenshot(
  url: string,
  outputPath: string
): Promise<boolean> {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.screenshot({ path: outputPath, fullPage: true });
  await browser.close();
  return true;
}

export async function extractSectionBoundingBoxes(
  url: string
): Promise<Section[]> {
  // Implementation similar to Python version
  // Use page.evaluate() instead of eval_on_selector_all
}

export async function takeSectionScreenshot(
  url: string,
  outputPath: string,
  selector: string
): Promise<boolean> {
  // Implementation using Playwright's element screenshot
}
```

#### 2.3 Image Processing
**File**: `src/utils/image-processing.ts`

Replace PIL with Sharp:

```typescript
import sharp from 'sharp';
import { readFile, writeFile } from 'fs/promises';

export async function generateDiffImage(
  beforePath: string,
  afterPath: string,
  diffOutputPath: string
): Promise<void> {
  // Use sharp for image processing
  // Similar logic to Python PIL version
}

export async function encodeImageCompressed(
  imagePath: string,
  options: {
    format?: 'webp' | 'jpeg' | 'png';
    maxDim?: number;
    quality?: number;
  } = {}
): Promise<string> {
  // Use sharp for compression and encoding
  // Return base64 string
}
```

#### 2.4 OpenAI Client
**File**: `src/services/openai-client.ts`

```typescript
import OpenAI from 'openai';
import { readFile } from 'fs/promises';

export class OpenAIClient {
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async analyzeVisualDifferences(
    baseImage: string,
    prImage: string,
    diffImage: string,
    sectionsAnalysis: string,
    prTitle?: string,
    prDescription?: string
  ): Promise<VisualAnalysis> {
    // Implementation using OpenAI Vision API
    // Similar to Python version but with TypeScript types
  }
}
```

#### 2.5 GitHub Client
**File**: `src/utils/github.ts`

```typescript
import { Octokit } from '@octokit/rest';

export class GitHubClient {
  private octokit: Octokit;

  constructor(token: string) {
    this.octokit = new Octokit({ auth: token });
  }

  async fetchPRMetadata(
    owner: string,
    repo: string,
    prNumber: number
  ): Promise<{ title: string; description: string }> {
    // Implementation using Octokit
  }

  async postPRComment(
    owner: string,
    repo: string,
    prNumber: number,
    body: string
  ): Promise<void> {
    // Implementation using Octokit
    // Handle finding/updating existing comments
  }
}
```

### Phase 3: Workflow Implementation

#### 3.1 Main Workflow (useWorkflow)
**File**: `src/workflows/visual-regression.ts`

```typescript
import { workflow } from 'workflow';

export const visualRegressionWorkflow = workflow(
  async (input: WorkflowInput) => {
    "use workflow";

    // Step 1: Fetch PR metadata
    const prMetadata = await fetchPRMetadata(input);

    // Step 2: Process pages (can be parallelized)
    const pageResults = await Promise.all(
      (input.pages || ['/']).map(pagePath =>
        processPage({
          ...input,
          pagePath,
          prMetadata
        })
      )
    );

    // Step 3: Analyze all pages
    const analyses = await Promise.all(
      pageResults.map(result => analyzePage(result, prMetadata))
    );

    // Step 4: Generate report
    const report = await generateReport(analyses, input);

    // Step 5: Send to Bruni API (if token provided)
    let reportUrl: string | undefined;
    if (input.bruniToken) {
      reportUrl = await sendToBruniAPI(report, input);
    }

    // Step 6: Post PR comment
    await postPRComment(report, reportUrl, input);

    return { success: true, reportUrl };
  }
);
```

#### 3.2 Step Functions
**File**: `src/steps/take-screenshots.ts`

```typescript
import { step } from 'workflow';
import { takeScreenshot } from '../utils/playwright';

export const takeScreenshotsStep = step(
  async (input: { baseUrl: string; prUrl: string; outputDir: string }) => {
    "use step";

    const baseScreenshot = `${input.outputDir}/base.png`;
    const prScreenshot = `${input.outputDir}/pr.png`;

    await Promise.all([
      takeScreenshot(input.baseUrl, baseScreenshot),
      takeScreenshot(input.prUrl, prScreenshot)
    ]);

    return { baseScreenshot, prScreenshot };
  }
);
```

**File**: `src/steps/analyze-visual.ts`

```typescript
import { step } from 'workflow';
import { OpenAIClient } from '../services/openai-client';

export const analyzeVisualStep = step(
  async (input: {
    baseScreenshot: string;
    prScreenshot: string;
    diffImage: string;
    sectionsAnalysis: string;
    prTitle?: string;
    prDescription?: string;
  }) => {
    "use step";

    const client = new OpenAIClient(process.env.OPENAI_API_KEY!);
    const analysis = await client.analyzeVisualDifferences(
      input.baseScreenshot,
      input.prScreenshot,
      input.diffImage,
      input.sectionsAnalysis,
      input.prTitle,
      input.prDescription
    );

    return analysis;
  }
);
```

### Phase 4: MCP Server Integration

#### 4.1 MCP Server Client
**File**: `src/services/mcp-server.ts`

```typescript
// For useWorkflow, we may need to:
// 1. Keep MCP server as a separate service
// 2. Use HTTP client to communicate with it
// 3. Or use Playwright directly without MCP

// Option 1: Keep MCP server running
export async function analyzeSectionsWithMCP(
  baseUrl: string,
  prUrl: string
): Promise<string> {
  // HTTP client to MCP server
  // Or use Playwright directly for section extraction
}

// Option 2: Direct Playwright (simpler)
export async function analyzeSectionsDirect(
  url: string
): Promise<string> {
  // Use Playwright + AI (Claude/GPT) directly
  // Similar to Python's extract_real_dom_info + Agent
}
```

**Recommendation**: Consider replacing MCP server with direct Playwright + AI calls for simplicity, or use a simpler MCP client if the server must remain.

### Phase 5: Rate Limiting

#### 5.1 Rate Limiter
**File**: `src/utils/rate-limiter.ts`

```typescript
export class RateLimiter {
  private lastCallTime = 0;
  private minInterval: number;

  constructor(callsPerMinute: number = 20) {
    this.minInterval = 60000 / callsPerMinute;
  }

  async wait(): Promise<void> {
    const now = Date.now();
    const delta = now - this.lastCallTime;
    if (delta < this.minInterval) {
      await new Promise(resolve =>
        setTimeout(resolve, this.minInterval - delta)
      );
    }
    this.lastCallTime = Date.now();
  }
}
```

### Phase 6: Deployment

#### 6.1 GitHub Action
**File**: `.github/workflows/visual-regression.yml`

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
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      - name: Run Visual Regression
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npm run workflow:visual-regression
```

#### 6.2 Vercel Deployment (if using useWorkflow)
```typescript
// app/api/workflows/visual-regression/route.ts
import { visualRegressionWorkflow } from '@/workflows/visual-regression';

export async function POST(request: Request) {
  const input = await request.json();
  const result = await visualRegressionWorkflow(input);
  return Response.json(result);
}
```

## Migration Checklist

### Phase 1: Setup ✅
- [ ] Initialize TypeScript project
- [ ] Set up project structure
- [ ] Configure TypeScript compiler
- [ ] Install all dependencies
- [ ] Set up environment variables

### Phase 2: Core Utilities ✅
- [ ] Migrate Playwright screenshot functions
- [ ] Migrate image processing (Sharp)
- [ ] Migrate section extraction
- [ ] Migrate diff generation
- [ ] Create TypeScript types

### Phase 3: Services ✅
- [ ] Implement OpenAI client
- [ ] Implement GitHub client (Octokit)
- [ ] Implement Bruni API client
- [ ] Implement MCP client or alternative
- [ ] Implement rate limiter

### Phase 4: Workflow Steps ✅
- [ ] Fetch PR metadata step
- [ ] Take screenshots step
- [ ] Extract sections step
- [ ] Generate diff step
- [ ] Analyze sections step
- [ ] Analyze visual step
- [ ] Generate report step
- [ ] Send report step
- [ ] Post PR comment step

### Phase 5: Main Workflow ✅
- [ ] Implement main workflow with useWorkflow
- [ ] Add error handling
- [ ] Add retry logic
- [ ] Add logging/observability

### Phase 6: Testing ✅
- [ ] Unit tests for utilities
- [ ] Integration tests for steps
- [ ] End-to-end workflow test
- [ ] Test with real PRs

### Phase 7: Deployment ✅
- [ ] Update GitHub Action
- [ ] Deploy to Vercel (if using useWorkflow)
- [ ] Update documentation
- [ ] Migration guide for users

## Key Differences & Considerations

### 1. Async/Await Patterns
- **Python**: Uses `asyncio` with async/await
- **TypeScript**: Native async/await, similar pattern
- **Impact**: Minimal - direct translation possible

### 2. Image Processing
- **Python**: PIL/Pillow with NumPy
- **TypeScript**: Sharp library
- **Impact**: Need to rewrite image diff logic, but Sharp is more performant

### 3. MCP Server
- **Python**: Uses `agents` library with MCP
- **TypeScript**: May need HTTP client or direct Playwright
- **Impact**: Consider simplifying to direct Playwright + AI calls

### 4. Rate Limiting
- **Python**: Decorator-based
- **TypeScript**: Class-based or middleware
- **Impact**: Similar functionality, different pattern

### 5. Error Handling
- **Python**: try/except with logging
- **TypeScript**: try/catch with better type safety
- **Impact**: Better type safety, but need to handle errors explicitly

### 6. Workflow Orchestration
- **Python**: Sequential async functions
- **TypeScript**: useWorkflow with "use step" directives
- **Impact**: Better observability, automatic retries, state persistence

## Benefits of Migration

1. **Observability**: useWorkflow provides built-in traces, logs, and metrics
2. **Reliability**: Automatic retries and state persistence
3. **Type Safety**: Full TypeScript support reduces runtime errors
4. **Performance**: Sharp is faster than PIL for image processing
5. **Ecosystem**: Better integration with modern JavaScript/TypeScript tools
6. **Maintainability**: More structured codebase with clear step boundaries

## Risks & Mitigation

### Risk 1: MCP Server Compatibility
- **Mitigation**: Test MCP client in TypeScript or use direct Playwright alternative

### Risk 2: Image Processing Differences
- **Mitigation**: Thoroughly test diff generation with Sharp

### Risk 3: API Rate Limits
- **Mitigation**: Implement proper rate limiting and retry logic

### Risk 4: GitHub API Changes
- **Mitigation**: Use official Octokit library with proper versioning

## Timeline Estimate

- **Phase 1-2**: 1 week (Setup & Core utilities)
- **Phase 3**: 1 week (Services)
- **Phase 4**: 1 week (Workflow steps)
- **Phase 5**: 1 week (Main workflow)
- **Phase 6**: 1 week (Testing)
- **Phase 7**: 3 days (Deployment)

**Total**: ~5-6 weeks for complete migration

## Next Steps

1. **Decision**: Choose Mastra.ai or useWorkflow (recommend useWorkflow)
2. **POC**: Create a minimal proof of concept with one page analysis
3. **Incremental Migration**: Migrate one component at a time
4. **Parallel Development**: Keep Python version running while migrating
5. **Testing**: Extensive testing with real PRs before full migration

## References

- [useWorkflow Documentation](https://useworkflow.dev/)
- [Mastra.ai Documentation](https://mastra.ai/) (if chosen)
- [Playwright TypeScript API](https://playwright.dev/docs/api/class-playwright)
- [Sharp Documentation](https://sharp.pixelplumbing.com/)
- [OpenAI Node.js SDK](https://github.com/openai/openai-node)
- [Octokit Documentation](https://octokit.github.io/rest.js/)

