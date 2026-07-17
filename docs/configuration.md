# Configuration

`searxng-mcp` is configured with environment variables and CLI flags.

CLI flags override environment-derived defaults.

## Core Connection Settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEARXNG_MCP_BASE_URL` | `http://127.0.0.1:8890` | Primary SearXNG backend (`SEARXNG_BASE_URL` is accepted as a fallback alias) |
| `SEARXNG_MCP_FALLBACK_BASE_URLS` | unset | Comma-separated fallback SearXNG backends |
| `SEARXNG_MCP_TRANSPORT` | `stdio` | `stdio`, `streamable-http`, or `sse` |
| `SEARXNG_MCP_HOST` | `127.0.0.1` | HTTP bind host |
| `SEARXNG_MCP_PORT` | `8811` | HTTP bind port |
| `SEARXNG_MCP_TRUST_ENV` | `false` | Whether `httpx` trusts proxy env vars |
| `SEARXNG_MCP_USER_AGENT` | `searxng-mcp/<version>` | User agent for outgoing requests |

### Per-host override (Claude Code plugin)

The Claude Code plugin ships a `SEARXNG_MCP_BASE_URL` default of `http://127.0.0.1:8890`
in its manifest. A plugin manifest's `env` takes precedence over your
`settings.json` `env`, and the cached manifest is overwritten on every plugin
update — so neither is a durable place to point the server at your own backend.

Instead, the launcher (`scripts/mcp-server.sh`) sources an optional file just
before starting the server, so its exports win over the manifest default and
survive updates. Create `~/.config/searxng-mcp/env` (or point
`SEARXNG_MCP_ENV_FILE` elsewhere):

```sh
export SEARXNG_MCP_BASE_URL=http://your-searxng-host:8890
export SEARXNG_MCP_FALLBACK_BASE_URLS=http://backup-host:8890
```

With no such file, the manifest default applies unchanged.

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

Flags override the matching env-derived defaults when set:

| Flag | Maps to |
| --- | --- |
| `--transport` | `SEARXNG_MCP_TRANSPORT` (`stdio` / `streamable-http` / `sse`) |
| `--base-url` | `SEARXNG_MCP_BASE_URL` |
| `--host` | `SEARXNG_MCP_HOST` |
| `--port` | `SEARXNG_MCP_PORT` |
| `--mount-path` | Path prefix for streamable-http / SSE (e.g. `/mcp`) |
| `--cache-dir` | `SEARXNG_MCP_CACHE_DIR` |
| `--search-timeout` | `SEARXNG_MCP_SEARCH_TIMEOUT` |
| `--fetch-timeout` | `SEARXNG_MCP_FETCH_TIMEOUT` |
| `--search-concurrency` | `SEARXNG_MCP_SEARCH_CONCURRENCY` |
| `--fetch-concurrency` | `SEARXNG_MCP_FETCH_CONCURRENCY` |
| `--search-cache-ttl` | `SEARXNG_MCP_SEARCH_CACHE_TTL` |
| `--fetch-cache-ttl` | `SEARXNG_MCP_FETCH_CACHE_TTL` |

## Practical Defaults

- keep the server on `stdio` for local clients
- use `streamable-http` only when you need a shared endpoint
- keep `fetch_*` behind a trusted boundary
- leave render automatic unless the page needs browser execution
- prefer `~/.config/searxng-mcp/env` for plugin backend overrides (survives updates)
