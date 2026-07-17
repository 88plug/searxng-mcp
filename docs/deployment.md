# Deployment

`searxng-mcp` supports local stdio, containerized, and HTTP deployments.

## Local `stdio`

Simplest and safest mode for a single trusted MCP client.

```bash
export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp --transport stdio
```

Or from a checkout:

```bash
uv run searxng-mcp --transport stdio
```

## Shared HTTP

Use `streamable-http` when multiple clients or a reverse proxy need a network
endpoint.

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp \
  --transport streamable-http --host 0.0.0.0 --port 8811
```

Path prefix (mount under a subpath):

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp \
  --transport streamable-http --host 0.0.0.0 --port 8811 \
  --mount-path /mcp
```

Clients typically connect to `http://host:8811/mcp` (or your mount path). See
[Client Configs](reference/client-configs.md#streamable-http-shared-deployment).

`sse` is also accepted as a transport for legacy clients; prefer
`streamable-http` for new deploys.

## Docker

Standard image defaults to streamable-http on port 8811:

```bash
git clone https://github.com/88plug/searxng-mcp.git
cd searxng-mcp
docker build -t searxng-mcp .
docker run --rm -p 8811:8811 --add-host=host.docker.internal:host-gateway \
  -e SEARXNG_MCP_BASE_URL=http://host.docker.internal:8890 \
  searxng-mcp
```

`host.docker.internal` reaches SearXNG on the host. On Linux, `--add-host=…:host-gateway`
makes that name resolve.

## Hardened Docker

Use `Dockerfile.prod` + `docker-compose.yml` for a tighter runtime posture:

- non-root user
- Chromium sandbox enabled (`SEARXNG_MCP_RENDER_SANDBOX=1`)
- read-only root filesystem + explicit tmpfs scratch
- dropped Linux capabilities (`cap_drop: ALL`)
- `no-new-privileges`
- persistent cache volume at `/data/cache`

```bash
cd searxng-mcp
docker build -f Dockerfile.prod -t searxng-mcp:prod .
cp docker-compose.env.example .env
# edit .env — set SEARXNG_MCP_BASE_URL if SearXNG is not on the host
docker compose up --build -d
```

Publish port defaults to `8811` (`SEARXNG_MCP_PUBLISH_PORT`). Confirm readiness
with the `health` tool or by calling the MCP endpoint from a client.

## Reverse proxy

If you expose `streamable-http` beyond a single host:

- terminate TLS externally
- restrict source networks
- enforce authentication
- log and rate-limit abusive clients
- keep SearXNG and the MCP server on a trusted network segment

`fetch_url` / `fetch_many` accept arbitrary client-supplied URLs — treat the
service like any SSRF-capable internal tool. Full guidance in
[Security](security.md).

## Operational notes

- Keep the SearXNG backend close (latency dominates search time)
- Set `SEARXNG_MCP_FALLBACK_BASE_URLS` only for backends you control
- Use `health` after deploy and config changes
- Benchmark before/after capacity changes: `uv run searxng-mcp-bench --rounds 3`
