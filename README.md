<div align="center">

# searxng-mcp

Token-efficient MCP server for SearXNG metasearch, for Claude Code and any MCP client that wants private web search and page extraction.

[![plugin-validate](https://github.com/88plug/searxng-mcp/actions/workflows/plugin-validate.yml/badge.svg)](https://github.com/88plug/searxng-mcp/actions/workflows/plugin-validate.yml)
[![License: FSL-1.1-ALv2](https://img.shields.io/badge/license-FSL--1.1--ALv2-blue?style=flat)](LICENSE.md)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?style=flat)](https://github.com/88plug/claude-code-plugins)
[![Docs](https://img.shields.io/badge/docs-online-2ea44f)](https://88plug.github.io/searxng-mcp/)

</div>

Connect your SearXNG instance to an LLM and get search, multi-query research, and readable page extraction as MCP tools. The server keeps model-visible output short and preserves full result payloads in hidden metadata, so you spend tokens on answers instead of raw HTML.

## Install

As a Claude Code plugin:

```text
/plugin marketplace add 88plug/claude-code-plugins
/plugin install searxng@88plug
```

Standalone, from any MCP client (no install step):

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

> [!NOTE]
> You need a reachable SearXNG instance. The server defaults to `http://127.0.0.1:8890`. Point it elsewhere with `SEARXNG_MCP_BASE_URL`.

## Quickstart

Run the server against a local SearXNG backend and confirm it is healthy:

```bash
export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

In your MCP client, call the `health` tool. A healthy backend returns status `ok: true` with backend, cache, and render details. Then call `search` with a query and you get a compact ranked result list, with the full payload kept in `_meta`.

Rendered fetch is included in the default install. If the host has Chromium or Chrome, the server uses it; otherwise the first rendered fetch bootstraps Playwright Chromium into the user cache automatically.

## What you get

- Compact model-visible output, with full details preserved in hidden `_meta`.
- Faster research through parallel search and fetch fan-out.
- Rendered extraction for JS-heavy pages, with no extra install flags.
- Self-hostable deployment for your own SearXNG-backed MCP server.

The server is thin by design. SearXNG does the search work; `searxng-mcp` handles tool shaping, caching, extraction, and transport.

## MCP tools

| Tool | What it does |
| --- | --- |
| `search` | Concise web search; full raw payload in `_meta`. |
| `search_many` | Parallel fan-out across queries, with dedupe and merged ranking. |
| `search_and_fetch` | Search plus source extraction in one call. |
| `research` | Multi-query search with batch fetches and merged, cited sources. |
| `fetch_url` | Readable page extraction with citations. |
| `fetch_many` | Parallel URL extraction with caching. |
| `health` | Backend, cache, and render status. |

Tools surface as `mcp__searxng__search`, `mcp__searxng__fetch_url`, and so on.

The server also exposes MCP resources and optional prompts:

- `searxng://config` — current settings, transport mode, and render support.
- `searxng://guide` — the available tools and when to use each.
- `quick_lookup`, `deep_research`, `research_workflow` — optional compatibility prompts for clients that support prompt surfaces.

## Transports and deployment

The server supports `stdio`, `streamable-http`, and `sse` transports.

Local `stdio` for desktop clients and private workflows:

```bash
SEARXNG_MCP_TRANSPORT=stdio uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

Streamable HTTP for a private service or team deployment:

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp \
  --transport streamable-http --host 0.0.0.0 --port 8811
```

From a checkout (contributor path):

```bash
uv sync
uv run searxng-mcp
```

### Docker

```bash
docker build -t searxng-mcp .
docker run --rm -p 8811:8811 --add-host=host.docker.internal:host-gateway \
  -e SEARXNG_MCP_BASE_URL=http://host.docker.internal:8890 \
  searxng-mcp
```

For a longer-running self-hosted service, use the hardened image and Compose stack:

```bash
docker build -f Dockerfile.prod -t searxng-mcp:prod .
cp docker-compose.env.example .env
docker compose up --build -d
```

> [!TIP]
> If you expose the HTTP transport, treat it like an internal service. `fetch_url` and `fetch_many` can request arbitrary client-supplied URLs, so put `streamable-http` behind auth or a reverse proxy and add the controls you would expect for any SSRF-capable tool. `SEARXNG_MCP_FETCH_VERIFY_TLS=0` is only for private or self-signed backends.

## Configuration

Set behavior through environment variables. The most common ones:

- `SEARXNG_MCP_BASE_URL` — SearXNG base URL. Default `http://127.0.0.1:8890`.
- `SEARXNG_MCP_FALLBACK_BASE_URLS` — comma-separated fallback SearXNG instances.
- `SEARXNG_MCP_TRANSPORT` — `stdio`, `streamable-http`, or `sse`.
- `SEARXNG_MCP_SEARCH_TIMEOUT` — backend search timeout, seconds.
- `SEARXNG_MCP_FETCH_TIMEOUT` — fetch timeout, seconds.
- `SEARXNG_MCP_SEARCH_CACHE_TTL` — search cache TTL, seconds.
- `SEARXNG_MCP_FETCH_CACHE_TTL` — fetch cache TTL, seconds.
- `SEARXNG_MCP_FETCH_VERIFY_TLS` — set to `0` to skip TLS verification on fetches.
- `SEARXNG_MCP_CACHE_DIR` — cache directory path.

<details>
<summary>Rendered fetch (Playwright) variables</summary>

- `SEARXNG_MCP_RENDER_TIMEOUT` — browser navigation timeout for rendered fetches.
- `SEARXNG_MCP_RENDER_WAIT_MS` — extra wait after DOM content load for rendered fetches.
- `SEARXNG_MCP_RENDER_CONCURRENCY` — concurrent rendered fetch limit.
- `SEARXNG_MCP_RENDER_HEADLESS` — set to `0` to show the browser.
- `SEARXNG_MCP_RENDER_BROWSER_PATH` — explicit Chromium or Chrome binary path.
- `SEARXNG_MCP_RENDER_SANDBOX` — set to `1` to keep Chromium sandboxing enabled.
- `SEARXNG_MCP_RENDER_BLOCK_RESOURCES` — set to `0` to allow images, fonts, stylesheets, and media during render.
- `SEARXNG_MCP_RENDER_AUTO_FALLBACK` — set to `0` to disable automatic rendered fallback.
- `SEARXNG_MCP_RENDER_AUTO_MIN_WORDS` — lower this to make auto-render more aggressive.
- `SEARXNG_MCP_RENDER_AUTO_MIN_CHARS` — lower this to make auto-render more aggressive.

</details>

## Client configs

Use one of these `command` shapes with any MCP client:

- `searxng-mcp` — when the entry point is on `PATH` (after `uv sync` from a checkout, or `pipx install`).
- `uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp` — runs straight from this repo, no install step.

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

The benchmark reports raw backend latency, token-visible output size, merged multi-query search latency, research latency, fetch extraction latency, rendered fetch latency, and batch variants.

## Documentation

- [Getting started](docs/getting-started.md)
- [Deployment](docs/deployment.md)
- [Security](docs/security.md)
- [Tool reference](docs/reference/tools.md)
- [Client configs](docs/reference/client-configs.md)
- [Comparison](docs/comparison.md)
- [Changelog](CHANGELOG.md)
- [SearXNG docs](https://docs.searxng.org/)

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md). To build and test from a checkout:

```bash
uv sync --all-groups
uv run pytest -q
uv run python -m compileall src
uv run mkdocs build --strict
```

## License

Released under the [Functional Source License, Version 1.1, ALv2 Future License](LICENSE.md) (`FSL-1.1-ALv2`).

Free to use, copy, modify, and redistribute for any purpose except a Competing Use — offering this software (or a substantially similar substitute) as a commercial product or service. Each released version converts to the Apache License 2.0 on the second anniversary of its release date.

For commercial-use inquiries outside the Permitted Purpose: claude@cryptoandcoffee.com.
