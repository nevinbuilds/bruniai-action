# BruniAI Workflow Diagrams

## Current Python Workflow (Sequential)

```mermaid
graph TD
    A[GitHub Action Trigger] --> B[Setup Environment]
    B --> C[Start MCP Server]
    C --> D[Fetch PR Metadata]
    D --> E{For Each Page}
    E --> F[Take Base Screenshot]
    F --> G[Take PR Screenshot]
    G --> H[Extract Section Bounding Boxes]
    H --> I[Generate Diff Image]
    I --> J[Store Page Result]
    J --> K{More Pages?}
    K -->|Yes| E
    K -->|No| L[Connect to MCP Server]
    L --> M{For Each Page Result}
    M --> N[Analyze Sections with MCP]
    N --> O[Extract Sections with IDs]
    O --> P[Capture Section Screenshots]
    P --> Q[Analyze Visual with GPT-4]
    Q --> R[Store Page Analysis]
    R --> S{More Pages?}
    S -->|Yes| M
    S -->|No| T[Generate Multi-Page Report]
    T --> U{Bruni Token?}
    U -->|Yes| V[Send Report to Bruni API]
    U -->|No| W[Post PR Comment]
    V --> W
    W --> X[Stop MCP Server]
    X --> Y[End]
```

## Proposed TypeScript Workflow (Parallelized)

```mermaid
graph TD
    A[Workflow Trigger] --> B[Fetch PR Metadata Step]
    B --> C[Process Pages in Parallel]

    C --> D1[Page 1: Take Screenshots]
    C --> D2[Page 2: Take Screenshots]
    C --> D3[Page N: Take Screenshots]

    D1 --> E1[Page 1: Extract Sections]
    D2 --> E2[Page 2: Extract Sections]
    D3 --> E3[Page N: Extract Sections]

    E1 --> F1[Page 1: Generate Diff]
    E2 --> F2[Page 2: Generate Diff]
    E3 --> F3[Page N: Generate Diff]

    F1 --> G1[Page 1: Analyze Sections]
    F2 --> G2[Page 2: Analyze Sections]
    F3 --> G3[Page N: Analyze Sections]

    G1 --> H1[Page 1: Analyze Visual]
    G2 --> H2[Page 2: Analyze Visual]
    G3 --> H3[Page N: Analyze Visual]

    H1 --> I[Aggregate Results]
    H2 --> I
    H3 --> I

    I --> J[Generate Report]
    J --> K{Bruni Token?}
    K -->|Yes| L[Send to Bruni API]
    K -->|No| M[Post PR Comment]
    L --> M
    M --> N[End]
```

## Detailed Step Breakdown (useWorkflow)

```mermaid
graph LR
    subgraph "Workflow Entry"
        A[visualRegressionWorkflow]
    end

    subgraph "Step 1: Metadata"
        B[fetchPRMetadata]
        B --> B1[Get PR Title]
        B --> B2[Get PR Description]
        B --> B3[Get Repository Info]
    end

    subgraph "Step 2: Page Processing"
        C[processPage Workflow]
        C --> C1[Take Screenshots]
        C --> C2[Extract Sections]
        C --> C3[Generate Diff]
        C --> C4[Analyze Sections]
        C --> C5[Analyze Visual]
    end

    subgraph "Step 3: Reporting"
        D[generateReport]
        D --> D1[Format Markdown]
        D --> D2[Calculate Overall Status]
        D --> D3[Combine Page Analyses]
    end

    subgraph "Step 4: API Submission"
        E[sendToBruniAPI]
        E --> E1[Compress Images]
        E --> E2[Encode Base64]
        E --> E3[POST to API]
        E --> E4[Get Report URL]
    end

    subgraph "Step 5: GitHub Integration"
        F[postPRComment]
        F --> F1[Find Existing Comment]
        F --> F2[Format Markdown]
        F --> F3[Update or Create]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
```

## Data Flow Diagram

```mermaid
graph TD
    subgraph "Input"
        I1[Base URL]
        I2[PR URL]
        I3[Pages Array]
        I4[PR Metadata]
    end

    subgraph "Screenshot Layer"
        S1[Base Screenshot PNG]
        S2[PR Screenshot PNG]
        S3[Section Screenshots]
    end

    subgraph "Image Processing"
        P1[Diff Image Generation]
        P2[Image Compression]
        P3[Base64 Encoding]
    end

    subgraph "Analysis Layer"
        A1[Section Structure Analysis]
        A2[Visual Difference Analysis]
        A3[Critical Issues Detection]
    end

    subgraph "Output"
        O1[Structured JSON Report]
        O2[Markdown Report]
        O3[GitHub PR Comment]
        O4[Bruni API Submission]
    end

    I1 --> S1
    I2 --> S2
    S1 --> P1
    S2 --> P1
    S1 --> P2
    S2 --> P2
    S3 --> P2

    P2 --> P3
    P3 --> A2

    I1 --> A1
    A1 --> A2
    I4 --> A2

    A2 --> A3
    A3 --> O1
    O1 --> O2
    O2 --> O3
    O1 --> O4
```

## Component Architecture

```mermaid
graph TB
    subgraph "Workflow Layer"
        W[Main Workflow]
    end

    subgraph "Step Layer"
        S1[Fetch Metadata Step]
        S2[Screenshot Step]
        S3[Section Analysis Step]
        S4[Visual Analysis Step]
        S5[Report Generation Step]
        S6[API Submission Step]
        S7[PR Comment Step]
    end

    subgraph "Service Layer"
        SV1[Playwright Service]
        SV2[OpenAI Service]
        SV3[GitHub Service]
        SV4[Bruni API Service]
        SV5[MCP Service]
    end

    subgraph "Utility Layer"
        U1[Image Processing]
        U2[Rate Limiter]
        U3[Type Definitions]
        U4[Error Handler]
    end

    W --> S1
    W --> S2
    W --> S3
    W --> S4
    W --> S5
    W --> S6
    W --> S7

    S2 --> SV1
    S3 --> SV5
    S4 --> SV2
    S6 --> SV4
    S7 --> SV3

    S2 --> U1
    S4 --> U2
    S1 --> U3
    S1 --> U4
    S2 --> U4
    S3 --> U4
    S4 --> U4
    S5 --> U4
    S6 --> U4
    S7 --> U4
```

## Error Handling Flow

```mermaid
graph TD
    A[Step Execution] --> B{Success?}
    B -->|Yes| C[Continue to Next Step]
    B -->|No| D{Error Type?}

    D -->|Rate Limit| E[Wait & Retry]
    D -->|Network Error| F[Retry with Backoff]
    D -->|Fatal Error| G[Log Error & Stop]
    D -->|Transient Error| H[Retry 3 Times]

    E --> I{Retries Left?}
    F --> I
    H --> I

    I -->|Yes| A
    I -->|No| J[Mark Step as Failed]

    J --> K{Workflow Critical?}
    K -->|Yes| G
    K -->|No| L[Continue with Partial Results]

    C --> M[End]
    L --> M
    G --> M
```

## Comparison: Current vs Proposed

### Current (Python)
```mermaid
graph LR
    A[Sequential Processing] --> B[Page 1]
    B --> C[Page 2]
    C --> D[Page 3]
    D --> E[All Pages Done]
    E --> F[Sequential Analysis]
    F --> G[Report]
```

### Proposed (TypeScript)
```mermaid
graph LR
    A[Parallel Processing] --> B[Page 1]
    A --> C[Page 2]
    A --> D[Page 3]
    B --> E[Analysis]
    C --> E
    D --> E
    E --> F[Report]
```

## Performance Comparison

| Aspect | Current (Python) | Proposed (TypeScript) |
|--------|------------------|----------------------|
| **Page Processing** | Sequential | Parallel |
| **Observability** | Logging only | Built-in traces & metrics |
| **Error Recovery** | Manual retries | Automatic retry logic |
| **State Persistence** | None | Automatic state saving |
| **Type Safety** | Runtime checks | Compile-time checks |
| **Image Processing** | PIL (slower) | Sharp (faster) |

## Migration Path Visualization

```mermaid
graph TD
    A[Current Python App] --> B[Phase 1: Setup]
    B --> C[Phase 2: Core Utils]
    C --> D[Phase 3: Services]
    D --> E[Phase 4: Steps]
    E --> F[Phase 5: Workflow]
    F --> G[Phase 6: Testing]
    G --> H[Phase 7: Deployment]
    H --> I[New TypeScript App]

    A -.->|Running in Parallel| J[Python Version]
    J -.->|Gradual Migration| I
```

