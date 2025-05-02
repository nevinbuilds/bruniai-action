import asyncio
import logging
import anyio
from contextlib import asynccontextmanager
from agents.mcp.server import MCPServerSse, MCPServerSseParams

logger = logging.getLogger("agent-runner")

@asynccontextmanager
async def managed_mcp_server():
    mcp_server = None
    try:
        # Increase timeout for MCP server connection
        mcp_server = MCPServerSse(params=MCPServerSseParams(
            url="http://localhost:8931/sse",
            request_timeout=30  # Increased from default 5 seconds to 30 seconds
        ))

        # Add initial wait time to ensure MCP server is fully started
        initial_wait = 10
        logger.info(f"Waiting {initial_wait} seconds for MCP server to fully start...")
        await asyncio.sleep(initial_wait)

        # Try to connect with retries
        max_retries = 3
        retry_delay = 5
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to MCP server (attempt {attempt}/{max_retries})...")
                await mcp_server.connect()
                logger.info("🔌 Connected to MCP server")
                break
            except anyio.WouldBlock as e:
                if attempt < max_retries:
                    logger.warning(f"MCP server not ready yet (attempt {attempt}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("MCP server failed to become ready after all retries")
                    raise
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Failed to connect to MCP server (attempt {attempt}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    raise

        yield mcp_server
    finally:
        if mcp_server:
            try:
                mcp_server.connection = None
                logger.info("🔌 Disconnected MCP server")
            except Exception as e:
                logger.error("Failed to disconnect MCP server: %s", e)
