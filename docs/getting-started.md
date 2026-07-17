# Getting Started

Shortest path from a running SearXNG instance to a usable `searxng-mcp` server.

## Prerequisites

- A reachable SearXNG instance (default: `http://127.0.0.1:8890`)
- Python 3.11+ if you run from source or `uvx`
- Optional: local Chromium or Chrome for faster first rendered fetch

## 1. Install

=== "Claude Code plugin"

    ```text
    /plugin marketplace add 88plug/claude-code-plugins
    /plugin install searxng@88plug
    ```

    The plugin launcher (`scripts/mcp-server.sh`) resolves `uv`, provisions
    Python ≥3.11, and runs the package from the local plugin install.

    To point at a non-default backend without editing the plugin cache, create
    `~/.config/searxng-mcp/env`:

    ```sh
    export SEARXNG_MCP_BASE_URL=http://your-searxng-host:8890
    ```

=== "uvx (any MCP client)"

    ```bash
    export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
    uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp
    ```

    Wire that command into your client's MCP config. Copy-paste shapes for
    Claude Desktop, Codex CLI, gemini-cli, and opencode are in
    [Client Configs](reference/client-configs.md).

=== "From source"

    ```bash
    git clone https://github.com/88plug/searxng-mcp.git
    cd searxng-mcp
    uv sync --group dev
    export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
    uv run searxng-mcp
    ```

## 2. Confirm health

Call the `health` tool from your MCP client. Expect:

- backend reachable
- cache path present
- render status (available / unavailable)

If backend is down, fix SearXNG reachability first (`SEARXNG_MCP_BASE_URL`).

## 3. First tools

| Goal | Tool |
| --- | --- |
| One known query | `search` |
| Search + page excerpts | `search_and_fetch` |
| Multi-angle investigation | `research` |
| Read a URL you already have | `fetch_url` |

Visible output is intentionally compact. Full payloads live in MCP `_meta`
(and `structuredContent` where the client surfaces it).

## Transports

| Mode | When |
| --- | --- |
| `stdio` (default) | Local desktop clients, single user |
| `streamable-http` | Shared service / reverse proxy |

HTTP example:

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp \
  --transport streamable-http --host 0.0.0.0 --port 8811
```

Treat exposed HTTP like any SSRF-capable internal service — see
[Security](security.md).

## Next

- [Installation](installation.md) — Docker, hardened Compose, pip
- [Configuration](configuration.md) — full env / flag reference
- [Tool Reference](reference/tools.md) — parameters and defaults
- [Client Configs](reference/client-configs.md) — per-client JSON/TOML
