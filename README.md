<div align="center">

# searxng-mcp

MCP server for SearXNG — privacy-respecting web search and page extraction for Claude Code, AI agents, and any MCP client.

[![plugin-validate](https://github.com/88plug/searxng-mcp/actions/workflows/plugin-validate.yml/badge.svg)](https://github.com/88plug/searxng-mcp/actions/workflows/plugin-validate.yml)
[![License: FSL-1.1-ALv2](https://img.shields.io/badge/license-FSL--1.1--ALv2-blue?style=flat)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-online-2ea44f)](https://88plug.github.io/searxng-mcp/)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?style=flat)](https://github.com/88plug/claude-code-plugins)
[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/88plug/searxng-mcp)

</div>

`searxng-mcp` is a token-efficient [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that connects your self-hosted [SearXNG](https://docs.searxng.org/) metasearch instance to Claude Code, Anthropic-compatible clients, and other LLM / AI-agent tooling. You get privacy-respecting web search across 70+ engines plus readable page extraction — without shipping raw HTML into the model context.

Search, multi-query research, and fetch tools keep model-visible output short. Full result payloads stay in hidden `_meta`, so tokens go to answers. Deploy via stdio for local Claude workflows, or streamable-http / Docker for a self-hosted MCP service with optional Playwright rendered fetch for JS-heavy pages.

## Install

Claude Code plugin (hub-first):

```text
/plugin marketplace add 88plug/claude-code-plugins
/plugin install searxng@88plug
```

### Grok Build

```text
grok plugin marketplace add 88plug/claude-code-plugins
grok plugin install searxng@88plug --trust
```


Standalone MCP server — any client, no install step:

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

> [!NOTE]
> You need a reachable SearXNG instance. Default base URL is `http://127.0.0.1:8890`. Override with `SEARXNG_MCP_BASE_URL`.

## Quickstart

Point the server at a local SearXNG backend and confirm it is healthy:

```bash
export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

In your MCP client, call `health`. A healthy backend returns `ok: true` with backend, cache, and render details. Then call `search` — you get a compact ranked list; the full payload stays in `_meta`.

Rendered fetch ships in the default install. If the host has Chromium or Chrome, the server uses it. Otherwise the first rendered fetch bootstraps Playwright Chromium into the user cache.

## Features

| Feature | Detail |
| --- | --- |
| Token-efficient MCP tools | Compact model-visible output; full payloads in hidden `_meta` |
| Parallel research | Multi-query search and fetch fan-out with dedupe and merged ranking |
| Rendered extraction | Playwright/Chromium path for JS-heavy pages; no extra install flags |
| Self-hosted deployment | stdio, streamable-http, SSE, Docker, and Compose for private MCP services |
| Thin by design | SearXNG does the search; this server shapes tools, cache, extract, transport |

## MCP tools

| Tool | What it does |
| --- | --- |
| `search` | Concise web search; full raw payload in `_meta` |
| `search_many` | Parallel fan-out across queries, with dedupe and merged ranking |
| `search_and_fetch` | Search plus source extraction in one call |
| `research` | Multi-query search with batch fetches and merged, cited sources |
| `fetch_url` | Readable page extraction with citations |
| `fetch_many` | Parallel URL extraction with caching |
| `health` | Backend, cache, and render status |

Tools surface as `mcp__searxng__search`, `mcp__searxng__fetch_url`, and so on.

Resources and optional prompts:

- `searxng://config` — current settings, transport mode, and render support
- `searxng://guide` — available tools and when to use each
- `quick_lookup`, `deep_research`, `research_workflow` — optional prompts for clients that support prompt surfaces

## Transports and deployment

Supports `stdio`, `streamable-http`, and `sse`.

Local stdio for desktop clients and private workflows:

```bash
SEARXNG_MCP_TRANSPORT=stdio uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

Streamable HTTP for a private service or team deployment:

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp \
  --transport streamable-http --host 0.0.0.0 --port 8811
```

### Docker

```bash
docker build -t searxng-mcp .
docker run --rm -p 8811:8811 --add-host=host.docker.internal:host-gateway \
  -e SEARXNG_MCP_BASE_URL=http://host.docker.internal:8890 \
  searxng-mcp
```

Hardened image and Compose for a longer-running self-hosted service:

```bash
docker build -f Dockerfile.prod -t searxng-mcp:prod .
cp docker-compose.env.example .env
docker compose up --build -d
```

> [!TIP]
> If you expose the HTTP transport, treat it like an internal service. `fetch_url` and `fetch_many` can request client-supplied URLs, so put `streamable-http` behind auth or a reverse proxy. Apply the same controls you would for any SSRF-capable tool. `SEARXNG_MCP_FETCH_VERIFY_TLS=0` is only for private or self-signed backends.

## Configuration

Common environment variables:

- `SEARXNG_MCP_BASE_URL` — SearXNG base URL. Default `http://127.0.0.1:8890`
- `SEARXNG_MCP_FALLBACK_BASE_URLS` — comma-separated fallback SearXNG instances
- `SEARXNG_MCP_TRANSPORT` — `stdio`, `streamable-http`, or `sse`
- `SEARXNG_MCP_SEARCH_TIMEOUT` — backend search timeout, seconds
- `SEARXNG_MCP_FETCH_TIMEOUT` — fetch timeout, seconds
- `SEARXNG_MCP_SEARCH_CACHE_TTL` — search cache TTL, seconds
- `SEARXNG_MCP_FETCH_CACHE_TTL` — fetch cache TTL, seconds
- `SEARXNG_MCP_FETCH_VERIFY_TLS` — set to `0` to skip TLS verification on fetches
- `SEARXNG_MCP_CACHE_DIR` — cache directory path

<details>
<summary>Rendered fetch (Playwright) variables</summary>

- `SEARXNG_MCP_RENDER_TIMEOUT` — browser navigation timeout for rendered fetches
- `SEARXNG_MCP_RENDER_WAIT_MS` — extra wait after DOM content load
- `SEARXNG_MCP_RENDER_CONCURRENCY` — concurrent rendered fetch limit
- `SEARXNG_MCP_RENDER_HEADLESS` — set to `0` to show the browser
- `SEARXNG_MCP_RENDER_BROWSER_PATH` — explicit Chromium or Chrome binary path
- `SEARXNG_MCP_RENDER_SANDBOX` — set to `1` to keep Chromium sandboxing enabled
- `SEARXNG_MCP_RENDER_BLOCK_RESOURCES` — set to `0` to allow images, fonts, stylesheets, and media
- `SEARXNG_MCP_RENDER_AUTO_FALLBACK` — set to `0` to disable automatic rendered fallback
- `SEARXNG_MCP_RENDER_AUTO_MIN_WORDS` — lower to make auto-render more aggressive
- `SEARXNG_MCP_RENDER_AUTO_MIN_CHARS` — lower to make auto-render more aggressive

</details>

## Client configs

Use either command shape with any MCP client:

- `searxng-mcp` — when the entry point is on `PATH` (after `uv sync` from a checkout, or `pipx install`)
- `uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp` — runs from this repo with no install step

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "searxng": {
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

See [client configs](docs/reference/client-configs.md) for Codex CLI, gemini-cli, and more.

## Benchmarks

```bash
uv run searxng-mcp-bench --rounds 3
```

Reports raw backend latency, token-visible output size, merged multi-query search latency, research latency, fetch extraction latency, rendered fetch latency, and batch variants.

## Documentation

Full site: **[88plug.github.io/searxng-mcp](https://88plug.github.io/searxng-mcp/)**

- [Getting started](docs/getting-started.md)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Deployment](docs/deployment.md)
- [Security](docs/security.md)
- [Tool reference](docs/reference/tools.md)
- [Client configs](docs/reference/client-configs.md)
- [Comparison](docs/comparison.md)
- [Changelog](CHANGELOG.md)
- [SearXNG docs](https://docs.searxng.org/)

## Development

From a checkout:

```bash
uv sync
uv run searxng-mcp
```

Build and test:

```bash
uv sync --all-groups
uv run pytest -q
uv run python -m compileall src
uv run mkdocs build --strict
```

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## License

Released under the [Functional Source License, Version 1.1, ALv2 Future License](LICENSE) (`FSL-1.1-ALv2`).

Free to use, copy, modify, and redistribute for any purpose except a Competing Use — offering this software (or a substantially similar substitute) as a commercial product or service. Each released version converts to the Apache License 2.0 on the second anniversary of its release date.

For commercial-use inquiries outside the Permitted Purpose: andrew@88plug.com.
