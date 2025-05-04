# Troubleshooting Guide

This guide helps you resolve common issues that may arise while using the Visual Regression Testing tool.

## Common Issues and Solutions

### 1. Installation Problems

#### Issue: Python Virtual Environment Setup

**Symptoms:**

- Error when creating virtual environment
- Package installation failures

**Solutions:**

1. Ensure Python 3.10 is installed:
   ```bash
   python3.10 --version
   ```
2. Create virtual environment with explicit Python version:
   ```bash
   python3.10 -m venv venv310
   ```
3. Activate the environment:
   ```bash
   source venv310/bin/activate  # On Windows: venv310\Scripts\activate
   ```

#### Issue: Playwright MCP Installation

**Symptoms:**

- npm installation errors
- MCP server not starting

**Solutions:**

1. Update npm:
   ```bash
   npm install -g npm@latest
   ```
2. Clear npm cache:
   ```bash
   npm cache clean --force
   ```
3. Reinstall MCP:
   ```bash
   npm uninstall -g @playwright/mcp
   npm install -g @playwright/mcp
   ```

### 2. Runtime Issues

#### Issue: MCP Server Connection

**Symptoms:**

- Connection refused errors
- Server not responding

**Solutions:**

1. Check if port 8931 is available:
   ```bash
   lsof -i :8931
   ```
2. Try a different port:
   ```bash
   npx @playwright/mcp@latest --port 8932
   ```
3. Ensure no firewall blocking the port

#### Issue: Status Updates

**Symptoms:**

- Missing status updates
- Incorrect status reporting

**Solutions:**

1. Check GitHub token scope
2. Verify workflow permissions
3. Review status update configuration

## Debugging Tips

1. **Check Logs**

   - Review console output
   - Check error messages
   - Look for stack traces

2. **Verify Environment**
   ```bash
   python3 -c "import sys; print(sys.version)"
   node --version
   npm --version
   ```

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [Configuration Guide](configuration.md)
2. Review the [Usage Examples](usage-examples.md)
3. Consult the project's issue tracker
4. Contact the maintainers

Remember to provide:

- Error messages
- Environment details
- Steps to reproduce
- Expected vs actual behavior
