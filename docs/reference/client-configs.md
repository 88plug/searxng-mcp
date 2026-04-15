# Client Configs

`searxng-mcp` is a stdio MCP server. Every config below assumes a SearXNG instance reachable at `http://127.0.0.1:8890` — change `SEARXNG_MCP_BASE_URL` to your own.

The two `command` shapes that work with every client:

- `searxng-mcp` — when the entry point is on `PATH` (e.g. after `uv sync` from a checkout, or `pipx install`).
- `uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp` — runs straight from this repo, no install step.

## Claude Code / Claude Desktop

`~/.claude.json` (Claude Code) or `claude_desktop_config.json` (Claude Desktop). For project-scoped wiring, use `.mcp.json` at the repo root.

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

Tools surface as `mcp__searxng__search`, `mcp__searxng__fetch_url`, etc.

## OpenAI Codex CLI

`~/.codex/config.toml`. The project must also be added to the `projects` trust list in the same file or per-project config is ignored.

```toml
[mcp_servers.searxng]
command = "uvx"
args = ["--from", "git+https://github.com/88plug/searxng-mcp", "searxng-mcp"]
startup_timeout_sec = 30

[mcp_servers.searxng.env]
SEARXNG_MCP_BASE_URL = "http://127.0.0.1:8890"
SEARXNG_MCP_TRANSPORT = "stdio"
```

`startup_timeout_sec = 30` covers the `uvx` cold-start. Codex does not surface MCP prompts; only tools and resources reach the model. Tools surface as `mcp__searxng__search`, etc.

## Google gemini-cli

`~/.gemini/settings.json` (user) or `.gemini/settings.json` (project).

```json
{
  "mcpServers": {
    "searxng": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/88plug/searxng-mcp", "searxng-mcp"],
      "env": {
        "SEARXNG_MCP_BASE_URL": "http://127.0.0.1:8890",
        "SEARXNG_MCP_TRANSPORT": "stdio"
      },
      "timeout": 30000
    }
  }
}
```

Tools surface as `mcp_searxng_search`, etc. Prompts appear as `/searxng.quick_lookup`. Resources appear under `/mcp` and can be `@`-mentioned.

## sst/opencode

`opencode.json` at the repo root or `~/.config/opencode/opencode.json`.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "searxng": {
      "type": "local",
      "command": ["uvx", "--from", "git+https://github.com/88plug/searxng-mcp", "searxng-mcp"],
      "environment": {
        "SEARXNG_MCP_BASE_URL": "http://127.0.0.1:8890",
        "SEARXNG_MCP_TRANSPORT": "stdio"
      },
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

`timeout: 30000` covers the `uvx` cold-start (opencode's default is 5000). Tools surface as `searxng_search`, etc. opencode does not enforce permission gating on MCP tool calls — `searxng-mcp` is read-only and safe.

## Streamable HTTP (shared deployment)

Use this when the server is shared across users or running behind a reverse proxy.

Server side:

```bash
SEARXNG_MCP_TRANSPORT=streamable-http \
SEARXNG_MCP_HOST=0.0.0.0 \
SEARXNG_MCP_PORT=8811 \
  uv run searxng-mcp
```

Client side, point the MCP client at the HTTP endpoint. Example for Claude Code / Claude Desktop:

```json
{
  "mcpServers": {
    "searxng": {
      "url": "http://your-host:8811/mcp"
    }
  }
}
```

Codex uses `url = "..."`; gemini-cli uses `httpUrl`; opencode uses `type: "remote"` with `url`.

## Docker-Based Client Path

If the client runs on the same host as a container, make the SearXNG backend reachable to the container and keep the URL on a trusted network. The hardened production stack in `docker-compose.yml` already exposes the streamable-http transport on port 8811.

## Operational Tips

- Keep the transport on `stdio` for local single-user setups; switch to `streamable-http` for shared deployments
- Set `SEARXNG_MCP_BASE_URL` explicitly instead of relying on the default
- Run `health` once after wiring a new client to confirm backend reachability and render-engine status
- For all four CLI clients, raise the per-server startup/timeout setting to 30 s if you use `uvx` (cold-start downloads can exceed the default)
- All visible tool output is intentionally compact. Full payloads live in the MCP `_meta` field; clients that surface `_meta` (or read `structuredContent`) get the complete data without spending visible tokens
