#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { compareUrls } from "./comparison-service.js";
import type { CompareUrlsInput } from "./types.js";

/**
 * MCP Server for BruniAI visual comparison functionality.
 *
 * Exposes a single tool: compare_urls
 * that performs visual analysis between two URLs.
 */
async function main() {
  // Initialize the MCP server.
  const server = new McpServer(
    {
      name: "bruniai",
      version: "0.1.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Set up error handling on underlying server.
  server.server.onerror = (error) => {
    console.error("[MCP Error]", error);
  };

  // Register the compare_urls tool.
  server.registerTool(
    "compare_urls",
    {
      description:
        "Compare two URLs visually and analyze differences. " +
        "Takes screenshots, generates diff images, analyzes sections, " +
        "and performs AI-powered visual analysis. Returns analysis " +
        "results with paths to generated images.",
      inputSchema: {
        baseUrl: z.string().describe("Base/reference URL to compare against"),
        previewUrl: z.string().describe("Preview/changed URL to analyze"),
        page: z
          .string()
          .default("/")
          .describe("Page path to compare (default: '/')")
          .optional(),
      },
    },
    async (args) => {
      try {
        // Validate input.
        const input: CompareUrlsInput = {
          baseUrl: args.baseUrl,
          previewUrl: args.previewUrl,
          page: args.page || "/",
        };

        if (!input.baseUrl || !input.previewUrl) {
          throw new Error("baseUrl and previewUrl are required");
        }

        // Validate OPENAI_API_KEY is set.
        if (!process.env.OPENAI_API_KEY) {
          throw new Error("OPENAI_API_KEY environment variable is required");
        }

        // Perform comparison.
        const result = await compareUrls(input);

        // Return results as JSON text content.
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  error: "Comparison failed",
                  message: errorMessage,
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // Connect to stdio transport.
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error("BruniAI MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
