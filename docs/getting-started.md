# Getting Started

This page gives the shortest path from a local SearXNG instance to a usable `searxng-mcp` server.

## Prerequisites

- Python 3.11 or newer
- A running SearXNG instance
- Optional: local Chromium or Chrome for faster first rendered fetch

## Local Development

The contributor path is the fastest way to validate the server from source:

```bash
cd searxng-mcp
uv sync --group dev
uv run searxng-mcp --help
```

If you prefer `pip`:

```bash
cd searxng-mcp
python -m pip install -e .
searxng-mcp --help
```

If the machine does not already have Chromium or Chrome, the first rendered fetch downloads Playwright Chromium into the user cache automatically.

## First Run

By default the server speaks `stdio` and points at a local SearXNG backend.

```bash
export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
searxng-mcp
```

To run it as a shared HTTP service:

```bash
searxng-mcp --transport streamable-http --host 0.0.0.0 --port 8811
```

## First Tool

Start with `search` if you already know the query.

Use `search_and_fetch` if you need search plus source reading in one step.

Use `research` if the answer needs multiple search variants and citations.

## Recommended Next Reads

- [Installation](installation.md)
- [Configuration](configuration.md)
- [Deployment](deployment.md)
- [Security](security.md)
- [Tool Reference](reference/tools.md)
