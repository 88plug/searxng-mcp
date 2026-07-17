# Installation

`searxng-mcp` ships as a Claude Code plugin and as a pure MCP server you can run
with `uvx`, from source, or in Docker. There is no PyPI release under this
project name (the bare `searxng-mcp` name on PyPI is unrelated).

## Requirements

- A reachable [SearXNG](https://docs.searxng.org/) instance
- Python ≥3.11 when using `uvx` or a source install
- Optional: Chromium/Chrome for faster first rendered fetch (otherwise Playwright Chromium downloads on first use)

## Claude Code plugin

```text
/plugin marketplace add 88plug/claude-code-plugins
/plugin install searxng@88plug
```

Enable marketplace auto-update if you want new releases at session start.

The plugin default backend is `http://127.0.0.1:8890`. Override without editing
the plugin cache — create `~/.config/searxng-mcp/env` (or set
`SEARXNG_MCP_ENV_FILE`):

```sh
export SEARXNG_MCP_BASE_URL=http://your-searxng-host:8890
export SEARXNG_MCP_FALLBACK_BASE_URLS=http://backup-host:8890
```

The launcher sources that file last so exports survive plugin updates. Details
are under [Configuration](configuration.md#per-host-override-claude-code-plugin).

## uvx (standalone)

No install step. Run straight from GitHub:

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp --help
```

With a backend:

```bash
export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
```

Rendered fetch is in the default dependency set. If the host has no Chromium or
Chrome, the first rendered fetch downloads Playwright Chromium into the user
cache.

## From source

```bash
git clone https://github.com/88plug/searxng-mcp.git
cd searxng-mcp
uv sync --group dev
uv run searxng-mcp --help
```

Editable pip install:

```bash
python -m pip install -e .
searxng-mcp --help
```

Contributor checks:

```bash
uv sync --all-groups
uv run pytest -q
uv run mkdocs build --strict
```

## Docker

Standard image (streamable-http on port 8811):

```bash
git clone https://github.com/88plug/searxng-mcp.git
cd searxng-mcp
docker build -t searxng-mcp .
docker run --rm -p 8811:8811 --add-host=host.docker.internal:host-gateway \
  -e SEARXNG_MCP_BASE_URL=http://host.docker.internal:8890 \
  searxng-mcp
```

## Hardened container

Production Dockerfile + Compose (non-root, read-only rootfs, dropped caps,
Chromium sandbox on):

```bash
cd searxng-mcp
docker build -f Dockerfile.prod -t searxng-mcp:prod .
cp docker-compose.env.example .env
docker compose up --build -d
```

Default publish port is `8811`. Override with `SEARXNG_MCP_PUBLISH_PORT` in
`.env`. Backend URL defaults to `http://host.docker.internal:8890`.

## Notes

- Default transport is `stdio` (local clients)
- Use `streamable-http` for shared / container deploy
- `dev` dependency group is for contributors, not end users
- Keep `fetch_*` behind a trusted boundary when exposing HTTP — see [Security](security.md)
