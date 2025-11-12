interface Args {
  baseUrl?: string;
  prUrl?: string;
  pages?: string;
  bruniToken?: string;
  bruniApiUrl?: string;
}

/**
 * Parse command-line arguments from process.argv.
 *
 * @returns
 *  The parsed arguments.
 */
export function parseArgs(): Args {
  const args: Record<string, string> = {};
  for (let i = 2; i < process.argv.length; i += 2) {
    const key = process.argv[i];
    const value = process.argv[i + 1];
    if (key?.startsWith("--")) {
      const argName = key.slice(2).replace(/-/g, "");
      if (value && !value.startsWith("--")) {
        args[argName] = value;
      }
    }
  }
  return {
    baseUrl: args.baseurl,
    prUrl: args.prurl,
    pages: args.pages,
    bruniToken: args.brunitoken,
    bruniApiUrl: args.bruniapiurl,
  };
}
