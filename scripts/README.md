# Deployment Script

Automated deployment script for publishing both `bruniai` and `bruniai-mcp-server` packages to npm.

## Usage

### Basic Deployment

Deploy with automatic patch version bump:

```bash
npm run deploy
```

### Version Bumping

Specify version bump type:

```bash
npm run deploy patch   # 0.1.0 -> 0.1.1 (default)
npm run deploy minor   # 0.1.0 -> 0.2.0
npm run deploy major   # 0.1.0 -> 1.0.0
```

### Custom Version

Deploy with a specific version:

```bash
npm run deploy -- --version=1.2.3
```

### Dry Run

Test the deployment process without publishing:

```bash
npm run deploy:dry-run
```

### Additional Options

Skip tests:

```bash
npm run deploy -- --skip-tests
```

Skip build:

```bash
npm run deploy -- --skip-build
```

Combine options:

```bash
npm run deploy minor --skip-tests --dry-run
```

## What the Script Does

1. **Checks git status** - Warns if there are uncommitted changes
2. **Runs tests** - Executes `npm test` (unless `--skip-tests` is used)
3. **Builds packages** - Runs `npm run build` (unless `--skip-build` is used)
4. **Updates versions** - Bumps version in all package.json files
5. **Publishes packages** - Publishes in order:
   - `bruniai` (core package)
   - `bruniai-mcp-server` (depends on bruniai)
6. **Creates git tag** - Creates an annotated tag (e.g., `v0.1.1`)
7. **Commits changes** - Commits version updates

## Prerequisites

- You must be logged into npm (`npm login`)
- Git must be initialized and configured
- All tests must pass (unless `--skip-tests` is used)
- Working directory should be clean (or you'll be prompted)

## Post-Deployment

After deployment, the script will remind you to:

1. Review changes: `git log -1`
2. Push changes: `git push origin <branch>`
3. Push tags: `git push origin v<version>`

