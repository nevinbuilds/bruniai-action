# bruniai-mcp

MCP (Model Context Protocol) server for BruniAI visual comparison functionality.

This package exposes visual comparison tools that can be used within Cursor and other MCP-compatible applications.

## Installation

```bash
npm install -g bruniai-mcp
```

## Usage

After installation, configure it in Cursor's MCP settings:

```json
{
  "mcpServers": {
    "bruniai": {
      "command": "bruniai-mcp-server",
      "env": {
        "OPENAI_API_KEY": "sk-your-api-key-here"
      }
    }
  }
}
```

## Development

### Building

First, build the parent package (bruniai) to generate the dist files:

```bash
cd ../..
npm run build
```

Then build this package:

```bash
npm run build
```

### Running Locally

```bash
npm run dev
```

## Documentation

See [../../docs/mcp-server.md](../../docs/mcp-server.md) for complete documentation.

