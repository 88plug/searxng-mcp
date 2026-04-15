# searxng-mcp

`searxng-mcp` is a fast, token-efficient MCP server for SearXNG.

It is built for agent-driven search and research workflows:

- `search` for one query
- `search_many` for parallel fan-out
- `search_and_fetch` for one-query research
- `research` for broader multi-query investigations
- `fetch_url` and `fetch_many` for source reading
- `health` for backend and render readiness

The server keeps model-visible output compact and stores the fuller payload in hidden metadata, which keeps prompts lean while preserving detail for clients that can consume it.

## What It Optimizes For

- Fast lookups from a local SearXNG instance
- Research workflows that need citations and readable excerpts
- Dual transport support: `stdio` for local use and `streamable-http` for shared deployment
- Optional rendered fetch for JavaScript-heavy pages
- Cache-backed repeated reads so follow-up questions stay fast

## Start Here

- Read [Getting Started](getting-started.md)
- Read [Installation](installation.md)
- Check [Configuration](configuration.md)
- Review [Security](security.md)
- See [Tool Reference](reference/tools.md)

## Built For Search

This docs site is intentionally query-shaped:

- `SearXNG MCP server`
- `uvx` and `Docker`
- `Claude Desktop` and other MCP clients
- `streamable-http`
- `self-hosted web search`
- `token-efficient research`

If you are deciding whether this is a fit, the short version is:

- use `stdio` for local clients
- use `streamable-http` for a shared service
- keep `fetch_*` behind a trusted deployment boundary
- use the render path only when pages need browser execution
