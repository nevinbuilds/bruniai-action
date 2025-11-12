# Migration Summary: Python to TypeScript

## Quick Reference

### Current Application
- **Language**: Python 3.10+
- **Purpose**: Visual regression testing for GitHub PRs
- **Key Features**:
  - Screenshot comparison
  - AI-powered visual analysis
  - Section-by-section analysis
  - Multi-page support
  - GitHub PR integration

### Proposed Migration
- **Framework**: Vercel useWorkflow (recommended) or Mastra.ai
- **Language**: TypeScript
- **Benefits**: Better observability, parallel processing, type safety, automatic retries

## Key Documents

1. **[Architecture Diagram](./architecture-diagram.md)** - Detailed current architecture
2. **[Migration Plan](./migration-plan.md)** - Step-by-step migration guide
3. **[Workflow Diagrams](./workflow-diagram.md)** - Visual flow representations

## Architecture Overview

### Current Flow (Simplified)
```
GitHub Action → Setup → Screenshots → Section Analysis → Visual Analysis → Report → PR Comment
```

### Proposed Flow (Simplified)
```
Workflow Trigger → Parallel Page Processing → Aggregate → Report → PR Comment
```

## Technology Mapping

| Python Component | TypeScript Equivalent |
|------------------|----------------------|
| `asyncio` | Native `async/await` |
| `playwright` (CLI) | `playwright` (Node.js API) |
| `PIL/Pillow` | `sharp` |
| `requests` | `@octokit/rest` |
| `agents` + MCP | Direct Playwright or MCP HTTP client |
| Manual retries | useWorkflow automatic retries |
| Logging | useWorkflow built-in observability |

## Core Workflows Identified

### 1. Screenshot Workflow
- **Input**: baseUrl, prUrl, pagePath
- **Output**: baseScreenshot, prScreenshot, diffImage
- **Parallelizable**: ✅ Yes (per page)

### 2. Section Analysis Workflow
- **Input**: baseUrl, prUrl
- **Output**: sectionsAnalysis (text)
- **Dependencies**: MCP Server or direct Playwright
- **Parallelizable**: ✅ Yes (per page)

### 3. Visual Analysis Workflow
- **Input**: Screenshots, sectionsAnalysis, PR metadata
- **Output**: VisualAnalysis (JSON)
- **Rate Limited**: 20 calls/minute
- **Parallelizable**: ⚠️ Limited (rate limiting)

### 4. Reporting Workflow
- **Input**: All page analyses
- **Output**: Markdown report, PR comment
- **Parallelizable**: ❌ No (sequential)

## Migration Phases

### Phase 1: Foundation (Week 1)
- Setup TypeScript project
- Install dependencies
- Create project structure
- Define types

### Phase 2: Core Utilities (Week 1-2)
- Playwright utilities
- Image processing (Sharp)
- GitHub client
- OpenAI client

### Phase 3: Services (Week 2)
- MCP client or alternative
- Rate limiter
- Error handling
- Logging

### Phase 4: Workflow Steps (Week 3)
- Implement all step functions
- Add error handling
- Add retry logic

### Phase 5: Main Workflow (Week 4)
- Integrate all steps
- Add parallelization
- Add observability

### Phase 6: Testing (Week 5)
- Unit tests
- Integration tests
- E2E tests

### Phase 7: Deployment (Week 5-6)
- GitHub Action update
- Vercel deployment (if useWorkflow)
- Documentation

## Key Decisions

### ✅ Recommended: useWorkflow
**Why?**
- Mature, production-ready
- Excellent observability
- Automatic retries and state persistence
- Great TypeScript support
- Active community

### ⚠️ Alternative: Mastra.ai
**When?** If you need more AI agent orchestration features

### MCP Server Strategy
**Option 1**: Keep MCP server, use HTTP client
**Option 2**: Replace with direct Playwright + AI calls (simpler)
**Recommendation**: Option 2 for simplicity

## Critical Considerations

### 1. Rate Limiting
- OpenAI API: 20 calls/minute
- Implement rate limiter before visual analysis step
- Consider request queuing for parallel pages

### 2. Image Processing
- Sharp is faster than PIL
- Need to rewrite diff generation logic
- Test thoroughly with various image sizes

### 3. Error Handling
- useWorkflow provides automatic retries
- Still need explicit error handling for fatal errors
- Consider circuit breakers for external APIs

### 4. State Management
- useWorkflow automatically persists state
- No need for manual state saving
- Workflows can resume from failures

### 5. Observability
- useWorkflow provides built-in traces
- Can see every step execution
- Better debugging than current Python logging

## Success Criteria

### Functional
- ✅ All current features working
- ✅ Multi-page support
- ✅ Section analysis
- ✅ Visual analysis
- ✅ PR comments
- ✅ Bruni API integration

### Non-Functional
- ✅ Performance: Same or better
- ✅ Reliability: Better (automatic retries)
- ✅ Observability: Better (built-in traces)
- ✅ Maintainability: Better (type safety)
- ✅ Developer Experience: Better (TypeScript)

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| MCP compatibility | Test early or use alternative |
| Image processing differences | Thorough testing |
| API rate limits | Proper rate limiting |
| Migration downtime | Parallel development |
| Breaking changes | Extensive testing |

## Next Steps

1. **Review documents** (this, architecture, migration plan, diagrams)
2. **Choose framework** (useWorkflow recommended)
3. **Create POC** (minimal workflow with one page)
4. **Get approval** (technical review)
5. **Start Phase 1** (project setup)

## Questions to Answer

1. **Deployment**: Vercel or self-hosted?
2. **MCP Server**: Keep or replace?
3. **Timeline**: 5-6 weeks acceptable?
4. **Parallel Development**: Keep Python version running?
5. **Testing**: How comprehensive?

## Resources

- [useWorkflow Docs](https://useworkflow.dev/)
- [Playwright TypeScript](https://playwright.dev/docs/api/class-playwright)
- [Sharp Documentation](https://sharp.pixelplumbing.com/)
- [OpenAI Node.js SDK](https://github.com/openai/openai-node)
- [Octokit Documentation](https://octokit.github.io/rest.js/)

## Contact & Support

For questions about migration:
- Review detailed migration plan
- Check architecture diagram
- Refer to workflow diagrams
- Test with POC first

---

**Last Updated**: [Date]
**Status**: Ready for Review
**Next Action**: Choose framework and create POC

