# Configuration

`searxng-mcp` is configured with environment variables and CLI flags.

CLI flags override environment-derived defaults.

## Core Connection Settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEARXNG_MCP_BASE_URL` | `http://127.0.0.1:8890` | Primary SearXNG backend |
| `SEARXNG_MCP_FALLBACK_BASE_URLS` | unset | Comma-separated fallback SearXNG backends |
| `SEARXNG_MCP_TRANSPORT` | `stdio` | `stdio`, `streamable-http`, or `sse` |
| `SEARXNG_MCP_HOST` | `127.0.0.1` | HTTP bind host |
| `SEARXNG_MCP_PORT` | `8811` | HTTP bind port |
| `SEARXNG_MCP_TRUST_ENV` | `false` | Whether `httpx` trusts proxy env vars |
| `SEARXNG_MCP_USER_AGENT` | `searxng-mcp/<version>` | User agent for outgoing requests |

## Timeouts and Caching

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEARXNG_MCP_SEARCH_TIMEOUT` | `6.0` | Search request timeout |
| `SEARXNG_MCP_FETCH_TIMEOUT` | `15.0` | Fetch request timeout |
| `SEARXNG_MCP_SEARCH_CACHE_TTL` | `30` | Search cache TTL in seconds |
| `SEARXNG_MCP_FETCH_CACHE_TTL` | `3600` | Fetch cache TTL in seconds |
| `SEARXNG_MCP_CACHE_DIR` | `~/.cache/searxng-mcp` | Local cache directory |
| `SEARXNG_MCP_CACHE_SIZE_LIMIT` | `268435456` | Cache size limit in bytes |

## Search Defaults

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEARXNG_MCP_DEFAULT_LANGUAGE` | `en` | Default language sent to SearXNG |
| `SEARXNG_MCP_DEFAULT_CATEGORIES` | `general` | Default category filter |
| `SEARXNG_MCP_DEFAULT_SAFESEARCH` | `0` | Default SearXNG safesearch level |
| `SEARXNG_MCP_DEFAULT_MAX_RESULTS` | `5` | Default visible result count |
| `SEARXNG_MCP_DEFAULT_EXCERPT_CHARS` | `1800` | Default excerpt length |

## Transport and Throughput

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEARXNG_MCP_SEARCH_CONCURRENCY` | `6` | Search fan-out concurrency |
| `SEARXNG_MCP_FETCH_CONCURRENCY` | `3` | Fetch fan-out concurrency |
| `SEARXNG_MCP_SEARCH_CONNECTIONS` | `32` | Outgoing search connections |
| `SEARXNG_MCP_SEARCH_KEEPALIVE` | `16` | Search keepalive pool |
| `SEARXNG_MCP_FETCH_CONNECTIONS` | `16` | Outgoing fetch connections |
| `SEARXNG_MCP_FETCH_KEEPALIVE` | `8` | Fetch keepalive pool |

## Render Settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEARXNG_MCP_FETCH_VERIFY_TLS` | `true` | Verify TLS on fetch requests |
| `SEARXNG_MCP_RENDER_TIMEOUT` | `18.0` | Browser render timeout |
| `SEARXNG_MCP_RENDER_WAIT_MS` | `1200` | Additional render wait after load |
| `SEARXNG_MCP_RENDER_CONCURRENCY` | `2` | Parallel browser sessions |
| `SEARXNG_MCP_RENDER_HEADLESS` | `true` | Run browser headless |
| `SEARXNG_MCP_RENDER_BROWSER_PATH` | unset | Explicit Chromium path |
| `SEARXNG_MCP_RENDER_SANDBOX` | `false` | Whether Chromium sandbox is enabled |
| `SEARXNG_MCP_RENDER_BLOCK_RESOURCES` | `true` | Block heavy page resources |
| `SEARXNG_MCP_RENDER_AUTO_FALLBACK` | `true` | Retry with rendered fetch for weak HTML pages |
| `SEARXNG_MCP_RENDER_AUTO_MIN_WORDS` | `60` | Auto-render word threshold |
| `SEARXNG_MCP_RENDER_AUTO_MIN_CHARS` | `800` | Auto-render character threshold |

## CLI Flags

The main flags are:

- `--transport`
- `--base-url`
- `--host`
- `--port`
- `--mount-path`
- `--cache-dir`
- `--search-timeout`
- `--fetch-timeout`
- `--search-concurrency`
- `--fetch-concurrency`
- `--search-cache-ttl`
- `--fetch-cache-ttl`

## Practical Defaults

- keep the server on `stdio` for local clients
- use `streamable-http` only when you need a shared endpoint
- keep `fetch_*` behind a trusted boundary
- leave render automatic unless the page needs browser execution
