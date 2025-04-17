import asyncio
import os
import time
import logging
import argparse
from functools import wraps
from contextlib import asynccontextmanager

from dotenv import load_dotenv
import openai
from openai import OpenAIError, RateLimitError
from agents import Agent, Runner
from agents.mcp.server import MCPServerSse, MCPServerSseParams
import anyio
from anyio import create_task_group, create_memory_object_stream

# ----------------- Setup -------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-runner")

# ----------------- Rate Limiting Decorator (Optional) -------------------
def rate_limit(calls_per_minute=20):
    min_interval = 60.0 / calls_per_minute
    last_call_time = 0

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_call_time
            now = time.time()
            delta = now - last_call_time
            if delta < min_interval:
                await asyncio.sleep(min_interval - delta)
            last_call_time = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

Runner.run = rate_limit()(Runner.run)

@asynccontextmanager
async def managed_mcp_server():
    mcp_server = None
    try:
        mcp_server = MCPServerSse(params=MCPServerSseParams(url="http://localhost:8931/sse"))
        await mcp_server.connect()
        logger.info("🔌 Connected to MCP server")
        yield mcp_server
    finally:
        if mcp_server:
            try:
                mcp_server.connection = None
                logger.info("🔌 Disconnected MCP server")
            except Exception as e:
                logger.error("Failed to disconnect MCP server: %s", e)

async def run_comparison(mcp_server, agent, prompt):
    try:
        result = await Runner.run(agent, prompt)
        logger.info("✅ Comparison completed.")
        if result.final_output:
            print("\nComparison Results:")
            print(result.final_output)
    except Exception as e:
        logger.error("Error during comparison: %s", e)
        raise

async def main():
    parser = argparse.ArgumentParser(description='Compare two URLs for visual differences')
    parser.add_argument('--base-url', required=True, help='Base URL to compare against')
    parser.add_argument('--pr-url', required=True, help='PR URL to compare')
    args = parser.parse_args()

    async with managed_mcp_server() as mcp_server:
        try:
            agent = Agent(
                name="URL Comparator",
                instructions="""Compare two webpages and report any significant differences.
                1. First visit the base URL and analyze its content
                2. Then visit the PR URL and compare it with the base URL
                3. Report any significant differences in layout, content, or functionality""",
                mcp_servers=[mcp_server]
            )

            prompt = f"""Please compare these two URLs and report any significant differences:
            Base URL: {args.base_url}
            PR URL: {args.pr_url}

            Focus on:
            - Visual layout changes
            - Content differences
            - Functional changes
            - Any broken elements or errors

            Provide a detailed comparison report."""

            logger.info("🧠 Starting comparison between URLs")
            logger.info("Base URL: %s", args.base_url)
            logger.info("PR URL: %s", args.pr_url)

            await run_comparison(mcp_server, agent, prompt)

        except RateLimitError as e:
            logger.error("🚫 Rate limit or quota hit: %s", e)
        except Exception as e:
            logger.exception("❗ Unexpected error occurred")

async def run_main():
    try:
        await main()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error("Fatal error: %s", e)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error("Fatal error: %s", e)
