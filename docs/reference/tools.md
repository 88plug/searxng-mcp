# Tool Reference

This page lists the MCP tools exposed by `searxng-mcp`.

All search and fetch tools return compact visible output with richer payloads hidden in metadata when the client supports it.

## `search`

Single-query SearXNG search.

Use it when you already know the query and want a compact answer fast.

Key parameters:

- `query`
- `categories`
- `engines`
- `enabled_engines`
- `disabled_engines`
- `language`
- `pageno`
- `time_range`
- `safesearch`
- `max_results`
- `ttl`

## `search_many`

Parallel search across query variants.

Use it when you want breadth before reading sources.

Key parameters:

- `queries`
- `concurrency`
- the same SearXNG filters as `search`

## `search_and_fetch`

Search first, then fetch the best hits.

Use it for one-query research where the result needs citations and readable excerpts.

Key parameters:

- `query`
- `fetch_limit`
- `fetch_excerpt_chars`
- `rendered`
- `render_wait_ms`

## `research`

Multi-query research workflow with merge, dedupe, and fetch.

Use it for broader investigations that need source verification.

Key parameters:

- `queries`
- `fetch_limit`
- `fetch_excerpt_chars`
- `rendered`
- `render_wait_ms`
- `concurrency`

## `fetch_url`

Fetch a single URL and extract readable content.

Use it when you already know the source URL.

Key parameters:

- `url`
- `max_excerpt_chars`
- `max_links`
- `rendered`
- `render_wait_ms`
- `ttl`

## `fetch_many`

Fetch multiple URLs in parallel.

Use it when you already have a list of sources and want the shortest path to readable excerpts.

Key parameters:

- `urls`
- `max_excerpt_chars`
- `max_links`
- `rendered`
- `render_wait_ms`
- `concurrency`

## `health`

Check backend readiness, cache status, and render availability.

Use it for deployment checks and troubleshooting.

## Resources

- `searxng://config` returns machine-readable configuration and capability data
- `searxng://guide` returns the built-in workflow guide

## Prompts

Prompt surfaces are compatibility helpers, not the primary interface.

- `quick_lookup`
- `deep_research`
- `research_workflow`
