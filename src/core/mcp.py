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
            request_timeout=60,  # Increased from 30 to 60 seconds
            connection_timeout=120,  # Added explicit connection timeout
            max_message_size=50 * 1024 * 1024  # Increased max message size to 50MB
        ))

        # Add initial wait time to ensure MCP server is fully started
        initial_wait = 15  # Increased from 10 to 15 seconds
        logger.info(f"Waiting {initial_wait} seconds for MCP server to fully start...")
        await asyncio.sleep(initial_wait)

        # Try to connect with retries
        max_retries = 5  # Increased from 3 to 5 retries
        retry_delay = 10  # Increased from 5 to 10 seconds
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to MCP server (attempt {attempt}/{max_retries})...")
                await mcp_server.connect()
                logger.info("🔌 Connected to MCP server")
                break
            except (anyio.WouldBlock, TimeoutError, ConnectionError) as e:
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
                await asyncio.wait_for(mcp_server.disconnect(), timeout=10)
                logger.info("🔌 Disconnected MCP server")
            except Exception as e:
                logger.error("Failed to disconnect MCP server: %s", e)
