# searxng-mcp

[![CI](https://github.com/88plug/searxng-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/88plug/searxng-mcp/actions/workflows/ci.yml)
[![Release](https://github.com/88plug/searxng-mcp/actions/workflows/release.yml/badge.svg)](https://github.com/88plug/searxng-mcp/actions/workflows/release.yml)
[![Pages](https://github.com/88plug/searxng-mcp/actions/workflows/pages.yml/badge.svg)](https://github.com/88plug/searxng-mcp/actions/workflows/pages.yml)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/88plug/searxng-mcp)

An MCP server for SearXNG that keeps the model-visible output short, preserves full result payloads in hidden metadata, and supports both local `stdio` clients and deployed `streamable-http` use.

## What you get

- `search` for concise web search with full raw payloads in `_meta`
- `search_many` for parallel fan-out, dedupe, and merged ranking
- `search_and_fetch` for search plus source extraction in one call
- `research` for multi-query search with batch fetches and merged sources
- `fetch_url` for readable page extraction with citations
- `fetch_many` for parallel URL extraction with caching
- `health` for backend, cache, and render status

The server is designed to be thin. SearXNG does the search work; `searxng-mcp` handles tool shaping, caching, extraction, and transport.

## Quick Start

### Install from a checkout

```bash
uv sync
uv run searxng-mcp
```

### Install with `uvx`

`searxng-mcp` is distributed from this repository (no PyPI release). The shortest path is:

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

Rendered fetch is included in the default install. If the host already has Chromium or Chrome, `searxng-mcp` uses it. Otherwise the first rendered fetch bootstraps Playwright Chromium into the user cache automatically.

### Run with Docker

```bash
docker build -t searxng-mcp .
docker run --rm -p 8811:8811 --add-host=host.docker.internal:host-gateway \
  -e SEARXNG_MCP_BASE_URL=http://host.docker.internal:8890 \
  searxng-mcp
```

### Claude Desktop example

```json
{
  "mcpServers": {
    "searxng-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/88plug/searxng-mcp", "searxng-mcp"],
      "env": {
        "SEARXNG_MCP_BASE_URL": "http://127.0.0.1:8890",
        "SEARXNG_MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

## Deployment Modes

### Local `stdio`

Use this for desktop clients and private workflows. It is the simplest and safest mode.

```bash
SEARXNG_MCP_TRANSPORT=stdio uv run searxng-mcp
```

### Streamable HTTP

Use this for a private service, a team deployment, or a reverse-proxied internal endpoint.

```bash
SEARXNG_MCP_TRANSPORT=streamable-http uv run searxng-mcp --host 0.0.0.0 --port 8811
```

### Hardened Docker and Compose

For a longer-running self-hosted service, use the hardened container variant and the provided Compose stack.

```bash
docker build -f Dockerfile.prod -t searxng-mcp:prod .
cp docker-compose.env.example .env
docker compose up --build -d
```

## Security and Trust

This project is safe for local and trusted-network use. It is not a drop-in public Internet service.

- `fetch_url` and `fetch_many` can fetch arbitrary URLs supplied by the client
- rendered extraction may launch Chromium against untrusted pages
- `streamable-http` should be put behind auth or a reverse proxy for any shared deployment
- `SEARXNG_MCP_FETCH_VERIFY_TLS=0` is only for private or self-signed backend setups

If you expose the HTTP transport, treat it like an internal service and add the controls you would expect for any SSRF-capable tool.

## Why This Exists

- compact model-visible output, with full details preserved in hidden metadata
- faster research workflows through parallel search and fetch fan-out
- rendered extraction for JS-heavy pages without extra install flags
- self-hostable deployment for people who want their own SearXNG-backed MCP server

## MCP Surface

- `searxng://config` exposes current settings, transport mode, and render support
- `searxng://guide` summarizes the available tools and when to use them
- `quick_lookup`, `deep_research`, and `research_workflow` are optional compatibility prompts for clients that support prompt surfaces

## Environment

Key variables:

- `SEARXNG_MCP_BASE_URL`: SearXNG base URL, default `http://127.0.0.1:8890`
- `SEARXNG_MCP_FALLBACK_BASE_URLS`: optional comma-separated fallback SearXNG instances
- `SEARXNG_MCP_TRANSPORT`: `stdio`, `streamable-http`, or `sse`
- `SEARXNG_MCP_SEARCH_TIMEOUT`: backend search timeout in seconds
- `SEARXNG_MCP_FETCH_TIMEOUT`: fetch timeout in seconds
- `SEARXNG_MCP_SEARCH_CACHE_TTL`: search cache TTL in seconds
- `SEARXNG_MCP_FETCH_CACHE_TTL`: fetch cache TTL in seconds
- `SEARXNG_MCP_FETCH_VERIFY_TLS`: set to `0` to skip TLS verification on fetches
- `SEARXNG_MCP_RENDER_TIMEOUT`: browser navigation timeout for rendered fetches
- `SEARXNG_MCP_RENDER_WAIT_MS`: extra wait after DOM content load for rendered fetches
- `SEARXNG_MCP_RENDER_CONCURRENCY`: concurrent rendered fetch limit
- `SEARXNG_MCP_RENDER_HEADLESS`: set to `0` to show the browser
- `SEARXNG_MCP_RENDER_BROWSER_PATH`: explicit Chromium or Chrome binary path
- `SEARXNG_MCP_RENDER_SANDBOX`: set to `1` to keep Chromium sandboxing enabled
- `SEARXNG_MCP_RENDER_BLOCK_RESOURCES`: set to `0` to allow images, fonts, stylesheets, and media during render
- `SEARXNG_MCP_RENDER_AUTO_FALLBACK`: set to `0` to disable automatic rendered fallback
- `SEARXNG_MCP_RENDER_AUTO_MIN_WORDS`: lower this to make auto-render more aggressive
- `SEARXNG_MCP_RENDER_AUTO_MIN_CHARS`: lower this to make auto-render more aggressive
- `SEARXNG_MCP_CACHE_DIR`: cache directory path

## Benchmarks

```bash
uv run searxng-mcp-bench --rounds 3
```

The benchmark reports:

- raw SearXNG backend latency
- token-visible search output size
- merged multi-query search latency
- multi-query research latency
- fetch extraction latency
- rendered fetch latency
- batch fetch extraction latency
- rendered batch fetch latency

## Documentation

- [Docs site overview](docs/index.md)
- [Getting started](docs/getting-started.md)
- [Deployment](docs/deployment.md)
- [Security](docs/security.md)
- [Tool reference](docs/reference/tools.md)
- [Client configs](docs/reference/client-configs.md)
- [Comparison](docs/comparison.md)
- [Changelog](CHANGELOG.md)
- [SearXNG docs](https://docs.searxng.org/)

## Build and Test

```bash
uv sync --all-groups
uv run pytest -q
uv run python -m compileall src
uv run mkdocs build --strict
```

## Dependency Maintenance

Manual checks:

```bash
uv lock --upgrade --dry-run
uvx --from pip-audit pip-audit
```

Automated checks:

- weekly Dependabot PRs for `uv` dependencies and GitHub Actions
- weekly `Dependency Health` workflow for vulnerability scanning and upgrade dry runs

## License

[Functional Source License, Version 1.1, ALv2 Future License](LICENSE.md)
(`FSL-1.1-ALv2`).

Free to use, copy, modify, and redistribute for any purpose *except* a Competing
Use — i.e. offering this software (or a substantially similar substitute) as a
commercial product or service. Each released version automatically converts to
the Apache License 2.0 on the second anniversary of its release date.

For commercial-use inquiries that fall outside the Permitted Purpose:
claude@cryptoandcoffee.com.
