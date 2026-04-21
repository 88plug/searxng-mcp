# Installation

`searxng-mcp` is distributed as a Python package and is also self-hostable in Docker.

## uvx

`searxng-mcp` is distributed straight from the GitHub repository — there is no PyPI release. The one-line install is:

```bash
uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp --help
```

Rendered fetch ships in the default install. If the machine does not already have Chromium or Chrome, the first rendered fetch downloads Playwright Chromium into the user cache automatically.

## From Source

For local development or contribution work:

```bash
git clone <repo-url>
cd searxng-mcp
uv sync --group dev
uv run searxng-mcp --help
```

For a plain editable install:

```bash
python -m pip install -e .
```

## Docker

The project ships a Dockerfile for self-hosting:

```bash
cd searxng-mcp
docker build -t searxng-mcp .
docker run --rm -p 8811:8811 \
  -e SEARXNG_MCP_BASE_URL=http://host.docker.internal:8890 \
  searxng-mcp
```

## Hardened Container

Use the production Dockerfile and Compose stack when you want a tighter runtime posture:

```bash
cd searxng-mcp
docker build -f Dockerfile.prod -t searxng-mcp:prod .
docker compose up --build -d
```

## Installation Notes

- rendered fetch is included in the default install
- `dev` is for contributors, not end users
- `stdio` is the default transport
- `streamable-http` is for deployment

If you want the fastest path for a local MCP client, use `uvx` after publish or `uv run` from source.
