# Running Tests

Follow these steps to run the test suite locally.

## Prerequisites

- Node.js 20 or higher
- npm (comes with Node.js)
- macOS/Linux shell commands shown; adapt as needed for Windows

## Running Tests

### Run All Tests

```bash
# From repo root
npm test
```

### Run Tests in Watch Mode

```bash
npm test -- --watch
```

### Run Tests with UI

```bash
npm run test:ui
```

This opens an interactive test UI in your browser.

### Run Tests with Coverage

```bash
npm run test:coverage
```

Coverage reports will be generated in the `coverage/` directory.

### Run Specific Test Files

```bash
# Run a specific test file
npm test -- tests/unit/test_main.test.ts

# Run tests matching a pattern
npm test -- -t "pr comments"
```

### Run Tests in Verbose Mode

```bash
npm test -- --reporter=verbose
```

## Notes

- Tests use Vitest as the test runner
- TypeScript files are automatically transpiled during test execution
- To stop on first failure, add `--bail` flag: `npm test -- --bail`
- To increase verbosity, use `--reporter=verbose` or `--reporter=dot`
- Coverage is configured via `vitest.config.ts`
