# Deployment

`searxng-mcp` supports local, containerized, and HTTP deployments.

## Local `stdio`

This is the simplest and safest mode for a single trusted MCP client.

```bash
export SEARXNG_MCP_BASE_URL=http://127.0.0.1:8890
searxng-mcp --transport stdio
```

## Shared HTTP

Use `streamable-http` when the server needs to be reachable by multiple clients or deployed behind a reverse proxy.

```bash
searxng-mcp --transport streamable-http --host 0.0.0.0 --port 8811
```

If you mount the server under a path prefix:

```bash
searxng-mcp --transport streamable-http --mount-path /mcp
```

## Docker

The standard Dockerfile is the easiest self-hosted container path:

```bash
docker build -t searxng-mcp .
docker run --rm -p 8811:8811 \
  -e SEARXNG_MCP_BASE_URL=http://host.docker.internal:8890 \
  searxng-mcp
```

## Hardened Docker

Use the production image and Compose stack when you want non-root execution and tighter runtime controls.

The hardened path is designed for:

- non-root execution
- Chromium sandbox enabled
- read-only container filesystem
- explicit temporary scratch space
- dropped Linux capabilities

## Reverse Proxy

If you expose `streamable-http` to other users, put it behind auth and a reverse proxy.

Recommended proxy behavior:

- terminate TLS externally
- restrict source networks
- enforce authentication
- log requests
- rate limit abusive clients

## Operational Notes

- keep the SearXNG backend close to the server
- set fallback backends only when you control them
- use `health` as a quick readiness check
- use the benchmark command before and after deployment changes
