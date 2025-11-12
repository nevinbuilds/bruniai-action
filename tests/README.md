# Testing Guide

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

## Running Tests

- Run all tests:
  ```bash
  npm test
   ```
- Run tests in watch mode:
  ```bash
  npm test -- --watch
   ```
- Run a specific test file:
  ```bash
  npm test tests/unit/test_types.test.ts
   ```
- Run tests with UI:
  ```bash
  npm run test:ui
   ```

## Coverage

- Run tests with coverage report:
  ```bash
  npm run test:coverage
   ```

## Adding New Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Name test files as `*.test.ts`
- Use Vitest conventions for test functions:
  ```typescript
  import { describe, it, expect } from "vitest";

  describe("MyFunction", () => {
    it("should do something", () => {
      expect(true).toBe(true);
    });
  });
  ```

## Test Patterns

### Mocking Modules
```typescript
import { vi } from "vitest";

vi.mock("../../src-typescript/module.js", () => ({
  functionName: vi.fn().mockReturnValue("value"),
}));
```

### Mocking Environment Variables
```typescript
import { vi } from "vitest";

vi.stubEnv("GITHUB_REPOSITORY", "org/repo");
```

### Mocking Fetch
```typescript
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: async () => ({ data: "value" }),
});
```

### Async Tests
```typescript
it("should handle async operations", async () => {
  const result = await myAsyncFunction();
  expect(result).toBeDefined();
});
```

## CI

Tests are automatically run on GitHub Actions for every push and pull request to `main`.
