# searxng-mcp

Token-efficient MCP server for SearXNG metasearch — private web search and page extraction for Claude Code and any MCP client.

[![plugin-validate](https://github.com/88plug/searxng-mcp/actions/workflows/plugin-validate.yml/badge.svg)](https://github.com/88plug/searxng-mcp/actions/workflows/plugin-validate.yml)
[![License: FSL-1.1-ALv2](https://img.shields.io/badge/license-FSL--1.1--ALv2-blue?style=flat)](https://github.com/88plug/searxng-mcp/blob/main/LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?style=flat)](https://github.com/88plug/claude-code-plugins)
[![GitHub](https://img.shields.io/badge/GitHub-88plug%2Fsearxng--mcp-181717?style=flat&logo=github)](https://github.com/88plug/searxng-mcp)
[![Docs](https://img.shields.io/badge/docs-online-blue?style=flat)](https://88plug.github.io/searxng-mcp/)

Connect your SearXNG instance to an LLM. You get search, multi-query research, and readable page extraction as MCP tools. Model-visible output stays short; full payloads live in hidden `_meta`.

## Install

Claude Code plugin (recommended):

```text
/plugin marketplace add 88plug/claude-code-plugins
/plugin install searxng@88plug
```

### Grok Build

```text
grok plugin marketplace add 88plug/claude-code-plugins
grok plugin install searxng@88plug --trust
```


Standalone, any MCP client (no install step):

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

!!! note
    You need a reachable SearXNG instance. Default backend is `http://127.0.0.1:8890`. Point elsewhere with `SEARXNG_MCP_BASE_URL`.

## Quickstart

```bash
export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

In your MCP client, call `health`. A healthy backend returns `ok: true` with backend, cache, and render details. Then call `search` with a query for a compact ranked list (full payload in `_meta`).

Rendered fetch ships in the default install. Local Chromium/Chrome is used when present; otherwise the first rendered fetch bootstraps Playwright Chromium into the user cache.

## MCP tools

| Tool | Use when |
| --- | --- |
| `search` | One query, compact ranked hits |
| `search_many` | Parallel query variants, merged ranking |
| `search_and_fetch` | One query plus source extraction |
| `research` | Multi-query investigation with citations |
| `fetch_url` | Read one known URL |
| `fetch_many` | Read several URLs in parallel |
| `health` | Backend / cache / render readiness |

Tools surface as `mcp__searxng__search`, `mcp__searxng__fetch_url`, and so on.

Also exposed:

- Resources: `searxng://config`, `searxng://guide`
- Prompts (compatibility): `quick_lookup`, `deep_research`, `research_workflow`

Full parameter tables live in the [Tool Reference](https://github.com/88plug/searxng-mcp/blob/main/reference/tools.md).

## Why this shape

| Capability | Detail |
| --- | --- |
| Token-efficient output | Compact model-facing text; full raw data in `_meta` |
| Research workflows | Fan-out search, merge/dedupe, fetch with citations |
| Rendered pages | Playwright auto-fallback for JS-heavy HTML |
| Dual transport | `stdio` for local clients; `streamable-http` for shared deploy |
| Self-hosted | Docker + hardened Compose; your SearXNG, your network |

## Where next

- [Getting Started](https://github.com/88plug/searxng-mcp/blob/main/getting-started.md) — shortest path from SearXNG to a working MCP server
- [Installation](https://github.com/88plug/searxng-mcp/blob/main/installation.md) — plugin, uvx, source, Docker
- [Configuration](https://github.com/88plug/searxng-mcp/blob/main/configuration.md) — env vars and CLI flags
- [Client Configs](https://github.com/88plug/searxng-mcp/blob/main/reference/client-configs.md) — Claude Desktop, Codex, gemini-cli, opencode
- [Deployment](https://github.com/88plug/searxng-mcp/blob/main/deployment.md) / [Security](https://github.com/88plug/searxng-mcp/blob/main/security.md) — HTTP exposure and hardening

## Features

| Feature | Detail |
| --- | --- |
| Token-efficient MCP tools | Compact model-visible output; full payloads in hidden `_meta` |
| Parallel research | Multi-query search and fetch fan-out with dedupe and merged ranking |
| Rendered extraction | Playwright/Chromium path for JS-heavy pages; no extra install flags |
| Self-hosted deployment | stdio, streamable-http, SSE, Docker, and Compose for private MCP services |
| Thin by design | SearXNG does the search; this server shapes tools, cache, extract, transport |

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

Contributions welcome. See [CONTRIBUTING.md](https://github.com/88plug/searxng-mcp/blob/main/CONTRIBUTING.md) and the [code of conduct](https://github.com/88plug/searxng-mcp/blob/main/CODE_OF_CONDUCT.md).
