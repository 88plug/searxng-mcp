# Client Configs

These examples show the common ways to point MCP clients at `searxng-mcp`.

## Claude Desktop

If `searxng-mcp` is already on your `PATH` (e.g. via `uv sync` from a checkout):

```json
{
  "mcpServers": {
    "searxng-mcp": {
      "command": "searxng-mcp",
      "env": {
        "SEARXNG_MCP_BASE_URL": "http://127.0.0.1:8890"
      }
    }
  }
}
```

To run straight from the GitHub source without any local install, point `uvx` at the repo:

```json
{
  "mcpServers": {
    "searxng-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/88plug/searxng-mcp", "searxng-mcp"],
      "env": {
        "SEARXNG_MCP_BASE_URL": "http://127.0.0.1:8890"
      }
    }
  }
}
```

## Codex

```toml
[mcp_servers.searxng-mcp]
command = "searxng-mcp"
args = []

[mcp_servers.searxng-mcp.env]
SEARXNG_MCP_BASE_URL = "http://127.0.0.1:8890"
SEARXNG_MCP_TRANSPORT = "stdio"
```

## Streamable HTTP

Use this mode when the server is deployed for multiple clients or behind a proxy.

Set:

- `SEARXNG_MCP_TRANSPORT=streamable-http`
- `SEARXNG_MCP_HOST=0.0.0.0`
- `SEARXNG_MCP_PORT=8811`

Then point your client at the HTTP endpoint exposed by the deployment.

## Docker-Based Client Path

If the client runs on the same host as the container, make the backend reachable to the container and keep the SearXNG URL on a trusted network.

## Operational Tips

- keep the transport default on `stdio` for local use
- prefer one server per trusted user or team
- set the base URL explicitly instead of relying on ambient defaults
- use `health` after wiring the client
